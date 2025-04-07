from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QMessageBox, QTabWidget,
                             QTableWidget, QTableWidgetItem, QDialog, QLineEdit, QDialogButtonBox,
                            QMessageBox, QInputDialog)
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

        # Сначала инициализируем кнопки управления
        self.add_project_btn = None
        self.edit_project_btn = None
        self.del_project_btn = None
        self.add_task_btn = None
        self.edit_task_btn = None
        self.del_task_btn = None

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

        # Сначала создаём кнопки управления
        self.setup_management_buttons()

        # Вкладка таймера
        self.setup_timer_tab()

        # Вкладка статистики
        self.setup_stats_tab()

    def setup_management_buttons(self):
        """Инициализация кнопок управления (без размещения в layout)"""
        self.add_project_btn = QPushButton("+ Проект")
        self.edit_project_btn = QPushButton("✎ Проект")
        self.del_project_btn = QPushButton("🗑 Проект")
        self.add_task_btn = QPushButton("+ Задача")
        self.edit_task_btn = QPushButton("✎ Задача")
        self.del_task_btn = QPushButton("🗑 Задача")

        # Подключаем сигналы
        self.add_project_btn.clicked.connect(self.add_project)
        self.edit_project_btn.clicked.connect(self.edit_project)
        self.del_project_btn.clicked.connect(self.delete_project)
        self.add_task_btn.clicked.connect(self.add_task)
        self.edit_task_btn.clicked.connect(self.edit_task)
        self.del_task_btn.clicked.connect(self.delete_task)

        # Изначально блокируем кнопки
        self.edit_project_btn.setEnabled(False)
        self.del_project_btn.setEnabled(False)
        self.add_task_btn.setEnabled(False)
        self.edit_task_btn.setEnabled(False)
        self.del_task_btn.setEnabled(False)

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

        # Кнопки управления проектами/задачами
        buttons_container = QWidget()
        mgmt_layout = QHBoxLayout(buttons_container)
        mgmt_layout.addWidget(self.add_project_btn)
        mgmt_layout.addWidget(self.edit_project_btn)
        mgmt_layout.addWidget(self.del_project_btn)
        mgmt_layout.addWidget(QLabel(" | "))
        mgmt_layout.addWidget(self.add_task_btn)
        mgmt_layout.addWidget(self.edit_task_btn)
        mgmt_layout.addWidget(self.del_task_btn)
        timer_layout.addWidget(buttons_container)

        # Таймер
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 36px;")
        timer_layout.addWidget(self.timer_label)

        # Кнопки управления таймером
        timer_buttons = QHBoxLayout()
        self.start_button = QPushButton("Старт")
        self.pause_button = QPushButton("Пауза")
        self.reset_button = QPushButton("Сброс")

        self.start_button.clicked.connect(self.start_timer)
        self.pause_button.clicked.connect(self.pause_timer)
        self.reset_button.clicked.connect(self.reset_timer)

        timer_buttons.addWidget(self.start_button)
        timer_buttons.addWidget(self.pause_button)
        timer_buttons.addWidget(self.reset_button)

        timer_layout.addLayout(timer_buttons)
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

        # Добавляем кнопки действий
        self.stats_table.setColumnCount(6)  # Добавляем колонку для действий
        self.stats_table.setHorizontalHeaderLabels(
            ["Проект", "Задача", "Время", "Дата", "Продуктивно", "Действия"])

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

            # Добавляем кнопку удаления
            btn = QPushButton("Удалить")
            btn.clicked.connect(lambda _, r=row_idx: self.delete_time_record(r))
            self.stats_table.setCellWidget(row_idx, 5, btn)

        self.stats_table.resizeColumnsToContents()

    def delete_time_record(self, row):
        record_id = self.stats_table.item(row, 0).data(Qt.UserRole)  # Сохраняем ID в данных

        reply = QMessageBox.question(
            self, 'Подтверждение',
            "Удалить запись времени?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.db.delete_time_record(record_id)
            self.update_stats_table()


    class ProjectDialog(QDialog):
        def __init__(self, parent=None, project=None):
            super().__init__(parent)
            self.setWindowTitle("Редактировать проект" if project else "Новый проект")

            layout = QVBoxLayout()
            self.name_edit = QLineEdit(project.name if project else "")
            layout.addWidget(QLabel("Название проекта:"))
            layout.addWidget(self.name_edit)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)

            self.setLayout(layout)

        def get_name(self):
            return self.name_edit.text().strip()

    class TaskDialog(QDialog):
        def __init__(self, parent=None, task=None):
            super().__init__(parent)
            self.setWindowTitle("Редактировать задачу" if task else "Новая задача")

            layout = QVBoxLayout()
            self.name_edit = QLineEdit(task.name if task else "")
            layout.addWidget(QLabel("Название задачи:"))
            layout.addWidget(self.name_edit)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)
            layout.addWidget(buttons)

            self.setLayout(layout)

        def get_name(self):
            return self.name_edit.text().strip()



    # Проекты
    def add_project(self):
        dialog = ProjectDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.get_name():
            self.db.add_project(dialog.get_name())
            self.update_projects_combo()

    def edit_project(self):
        if not self.project_combo.currentData():
            return

        project_id = self.project_combo.currentData()
        projects = self.db.get_projects()
        project = next((p for p in projects if p.id == project_id), None)

        if project:
            dialog = ProjectDialog(self, project)
            if dialog.exec_() == QDialog.Accepted and dialog.get_name():
                # Обновляем проект в БД
                cursor = self.db.conn.cursor()
                cursor.execute(
                    "UPDATE projects SET name = ? WHERE id = ?",
                    (dialog.get_name(), project.id)
                )
                self.db.conn.commit()
                self.update_projects_combo()

    def delete_project(self):
        if not self.project_combo.currentData():
            return

        reply = QMessageBox.question(
            self, 'Подтверждение',
            "Удалить проект и все связанные задачи?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)

        if reply == QMessageBox.Yes:
            project_id = self.project_combo.currentData()
            # Удаляем сначала задачи, затем проект
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            self.db.conn.commit()
            self.update_projects_combo()
            self.task_combo.clear()

    # Задачи
    def add_task(self):
        if not self.project_combo.currentData():
            QMessageBox.warning(self, "Ошибка", "Сначала выберите проект!")
            return

        dialog = TaskDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.get_name():
            project_id = self.project_combo.currentData()
            self.db.add_task(project_id, dialog.get_name())
            self.update_tasks_combo()

    def edit_task(self):
        if not self.task_combo.currentData():
            return

        task_id = self.task_combo.currentData()
        tasks = self.db.get_tasks_for_project(self.project_combo.currentData())
        task = next((t for t in tasks if t.id == task_id), None)

        if task:
            dialog = TaskDialog(self, task)
            if dialog.exec_() == QDialog.Accepted and dialog.get_name():
                # Обновляем задачу в БД
                cursor = self.db.conn.cursor()
                cursor.execute(
                    "UPDATE tasks SET name = ? WHERE id = ?",
                    (dialog.get_name(), task.id)
                )
                self.db.conn.commit()
                self.update_tasks_combo()

    def delete_task(self):
        if not self.task_combo.currentData():
            return

        reply = QMessageBox.question(
            self, 'Подтверждение',
            "Удалить задачу и все связанные записи времени?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)

        if reply == QMessageBox.Yes:
            task_id = self.task_combo.currentData()
            # Удаляем сначала записи времени, затем задачу
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM time_records WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.db.conn.commit()
            self.update_tasks_combo()

    def update_projects_combo(self):
        self.project_combo.clear()
        projects = self.db.get_projects()
        for project in projects:
            self.project_combo.addItem(project.name, project.id)

        # Блокируем кнопки если нет проектов
        has_projects = len(projects) > 0
        self.edit_project_btn.setEnabled(has_projects)
        self.del_project_btn.setEnabled(has_projects)
        self.add_task_btn.setEnabled(has_projects)

    def update_tasks_combo(self):
        self.task_combo.clear()
        project_id = self.project_combo.currentData()
        if project_id:
            tasks = self.db.get_tasks_for_project(project_id)
            for task in tasks:
                self.task_combo.addItem(task.name, task.id)

        # Блокируем кнопки если нет задач
        has_tasks = self.task_combo.count() > 0
        self.edit_task_btn.setEnabled(has_tasks)
        self.del_task_btn.setEnabled(has_tasks)