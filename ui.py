from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QMessageBox, QTabWidget,
                             QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QTimer, Qt
from models import Project, Task, TimeRecord
from database import Database
from timer_logic import Timer
from datetime import datetime


class TimerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.timer = Timer(self.on_timer_end)
        self.current_task_id = None
        self.setup_ui()
        self.setup_timers()

    def setup_ui(self):
        self.setWindowTitle("Task Timer")
        self.setGeometry(100, 100, 600, 400)

        # Главный виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Вкладки
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Вкладка таймера
        self.setup_timer_tab()

        # Вкладка статистики
        self.setup_stats_tab()

    def setup_timer_tab(self):
        timer_tab = QWidget()
        timer_layout = QVBoxLayout(timer_tab)

        # Выбор проекта
        self.project_combo = QComboBox()
        self.update_projects_combo()
        timer_layout.addWidget(QLabel("Проект:"))
        timer_layout.addWidget(self.project_combo)

        # Выбор задачи
        self.task_combo = QComboBox()
        timer_layout.addWidget(QLabel("Задача:"))
        timer_layout.addWidget(self.task_combo)
        self.project_combo.currentIndexChanged.connect(self.update_tasks_combo)

        # Таймер
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 36px;")
        timer_layout.addWidget(self.timer_label)

        # Кнопки управления
        buttons_layout = QHBoxLayout()

        self.start_button = QPushButton("Старт")
        self.start_button.clicked.connect(self.start_timer)
        buttons_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("Пауза")
        self.pause_button.clicked.connect(self.pause_timer)
        buttons_layout.addWidget(self.pause_button)

        self.reset_button = QPushButton("Сброс")
        self.reset_button.clicked.connect(self.reset_timer)
        buttons_layout.addWidget(self.reset_button)

        timer_layout.addLayout(buttons_layout)
        self.tabs.addTab(timer_tab, "Таймер")

    def setup_stats_tab(self):
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)

        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(5)
        self.stats_table.setHorizontalHeaderLabels(["Проект", "Задача", "Время", "Дата", "Продуктивно"])
        stats_layout.addWidget(self.stats_table)

        self.tabs.addTab(stats_tab, "Статистика")
        self.update_stats_table()

    def setup_timers(self):
        # Таймер для обновления отображения
        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(1000)  # Обновление каждую секунду

        # Таймер для проверки времени работы
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_work_time)
        self.check_timer.start(1000)  # Проверка каждую секунду

    def update_projects_combo(self):
        self.project_combo.clear()
        projects = self.db.get_projects()
        for project in projects:
            self.project_combo.addItem(project.name, project.id)

    def update_tasks_combo(self):
        self.task_combo.clear()
        project_id = self.project_combo.currentData()
        if project_id:
            tasks = self.db.get_tasks_for_project(project_id)
            for task in tasks:
                self.task_combo.addItem(task.name, task.id)

    def update_display(self):
        elapsed = self.timer.get_elapsed_time()
        self.timer_label.setText(self.timer.format_time(elapsed))

    def check_work_time(self):
        if self.timer.is_running:
            self.timer.check_timer()

    def start_timer(self):
        if self.task_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу!")
            return

        self.current_task_id = self.task_combo.currentData()
        self.timer.start()

    def pause_timer(self):
        self.timer.pause()

    def reset_timer(self):
        self.timer.reset()

    def on_timer_end(self, elapsed_seconds: int):
        reply = QMessageBox.question(
            self, 'Подтверждение',
            "Вы работали?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        was_productive = reply == QMessageBox.Yes

        if was_productive:
            start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.add_time_record(
                task_id=self.current_task_id,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=elapsed_seconds,
                was_productive=was_productive
            )
            self.update_stats_table()

        self.timer.reset()

    def update_stats_table(self):
        self.stats_table.setRowCount(0)

        # Получаем все записи времени с информацией о проектах и задачах
        cursor = self.db.conn.cursor()
        cursor.execute('''
        SELECT p.name AS project_name, t.name AS task_name, 
               tr.duration_seconds, tr.start_time, tr.was_productive
        FROM time_records tr
        JOIN tasks t ON tr.task_id = t.id
        JOIN projects p ON t.project_id = p.id
        ORDER BY tr.start_time DESC
        ''')

        for row_idx, row in enumerate(cursor.fetchall()):
            self.stats_table.insertRow(row_idx)

            project_item = QTableWidgetItem(row[0])
            task_item = QTableWidgetItem(row[1])

            # Форматируем время
            hours, remainder = divmod(row[2], 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            time_item = QTableWidgetItem(time_str)

            date_item = QTableWidgetItem(row[3])
            productive_item = QTableWidgetItem("Да" if row[4] else "Нет")

            self.stats_table.setItem(row_idx, 0, project_item)
            self.stats_table.setItem(row_idx, 1, task_item)
            self.stats_table.setItem(row_idx, 2, time_item)
            self.stats_table.setItem(row_idx, 3, date_item)
            self.stats_table.setItem(row_idx, 4, productive_item)

        self.stats_table.resizeColumnsToContents()