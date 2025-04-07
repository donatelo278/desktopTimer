from PyQt5.QtMultimedia import QSound
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QMessageBox, QTabWidget,
                             QTableWidget, QTableWidgetItem, QDialog, QLineEdit, QDialogButtonBox,
                             QMessageBox, QInputDialog, QAction, QCheckBox, QSpinBox)
from PyQt5.QtCore import QTimer, Qt, QUrl
from models import Project, Task, TimeRecord
from database import Database
from settings import Settings
from timer_logic import Timer
from datetime import datetime, timedelta


class TimerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.settings.load()
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

        self.sound_effect = QSoundEffect()
        self.sound_effect.setSource(QUrl.fromLocalFile("alert.wav"))

    def save_settings(self, dialog):
        # Сохраняем настройки
        self.settings.check_interval = self.interval_spinbox.value() * 60
        self.settings.enable_sound = self.sound_checkbox.isChecked()
        self.settings.save()

        # Перезапускаем таймер с новыми настройками
        self.check_timer.stop()
        self.check_timer.start(self.settings.check_interval * 1000)

        dialog.accept()
        QMessageBox.information(self, "Сохранено", "Настройки успешно сохранены!")

    def show_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки")
        layout = QVBoxLayout()

        # Настройка интервала проверки
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Интервал проверки активности (минут):")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 120)  # от 1 до 120 минут
        self.interval_spinbox.setValue(self.settings.check_interval // 60)
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spinbox)
        layout.addLayout(interval_layout)

        # Настройка звукового уведомления
        self.sound_checkbox = QCheckBox("Включить звуковое уведомление")
        self.sound_checkbox.setChecked(self.settings.enable_sound)
        layout.addWidget(self.sound_checkbox)

        # Кнопки OK/Отмена
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self.save_settings(dialog))
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        dialog.exec_()

    def setup_settings_menu(self):
        menubar = self.menuBar()
        settings_menu = menubar.addMenu('Настройки')

        # Настройка интервала проверки
        interval_action = QAction('Интервал проверки активности...', self)
        interval_action.triggered.connect(self.change_check_interval)
        settings_menu.addAction(interval_action)

        # Включение звука
        self.sound_action = QAction('Звуковое уведомление', self, checkable=True)
        self.sound_action.setChecked(self.settings.enable_sound)
        self.sound_action.triggered.connect(self.toggle_sound)
        settings_menu.addAction(self.sound_action)

    def change_check_interval(self):
        minutes, ok = QInputDialog.getInt(
            self, 'Настройка интервала',
            'Интервал проверки активности (минуты):',
            value=self.settings.check_interval // 60,
            min=1, max=120, step=1)

        if ok:
            self.settings.check_interval = minutes * 60
            self.settings.save()
            # Перезапускаем таймер с новым интервалом
            self.check_timer.stop()
            self.check_timer.start(self.settings.check_interval * 1000)
            QMessageBox.information(self, "Сохранено",
                                    f"Новый интервал проверки: {minutes} минут")

    def change_interval(self):
        minutes, ok = QInputDialog.getInt(
            self, 'Настройка интервала',
            'Интервал проверки активности (минуты):',
            value=self.settings.check_interval // 60,
            min=1, max=120
        )
        if ok:
            self.settings.check_interval = minutes * 60
            self.settings.save()
            self.check_timer.setInterval(self.settings.check_interval * 1000)

    def toggle_sound(self, checked):
        self.settings.enable_sound = checked
        self.settings.save()

    def setup_ui(self):
        self.setWindowTitle("Task Timer")
        self.setGeometry(100, 100, 600, 400)
        self.setup_settings_menu()

        # Главный виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Вкладки
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Сначала инициализируем кнопки управления
        self.setup_management_buttons()

        # Затем создаем вкладки
        self.setup_timer_tab()  # This initializes task_combo
        self.setup_stats_tab()

        # Теперь можно безопасно обновлять комбобоксы
        self.update_projects_combo()  # Moved after setup_timer_tab()

    def setup_management_buttons(self):
        """Инициализация кнопок управления"""
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
        timer_layout.addWidget(QLabel("Проект:"))
        timer_layout.addWidget(self.project_combo)

        # Выбор задачи
        self.task_combo = QComboBox()
        timer_layout.addWidget(QLabel("Задача:"))
        timer_layout.addWidget(self.task_combo)
        self.project_combo.currentIndexChanged.connect(self.update_tasks_combo)

        # Теперь, когда оба комбобокса созданы, можно их заполнить
        self.update_projects_combo()  # Перенесено после создания task_combo

        # Остальной код остается без изменений...
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
        self.stop_button = QPushButton("Стоп")  # Новая кнопка
        self.reset_button = QPushButton("Сброс")

        self.start_button.clicked.connect(self.start_timer)
        self.pause_button.clicked.connect(self.pause_timer)
        self.stop_button.clicked.connect(self.stop_timer)  # Новый обработчик
        self.reset_button.clicked.connect(self.reset_timer)

        timer_buttons.addWidget(self.start_button)
        timer_buttons.addWidget(self.pause_button)
        timer_buttons.addWidget(self.stop_button)
        timer_buttons.addWidget(self.reset_button)

        timer_layout.addLayout(timer_buttons)
        self.tabs.addTab(timer_tab, "Таймер")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)

    def setup_stats_tab(self):
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)

        # Фильтры
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)

        self.filter_project_combo = QComboBox()
        self.filter_project_combo.addItem("Все проекты", None)
        self.filter_task_combo = QComboBox()
        self.filter_task_combo.addItem("Все задачи", None)

        self.filter_project_combo.currentIndexChanged.connect(
            lambda: self.update_filter_task_combo())

        filter_layout.addWidget(QLabel("Проект:"))
        filter_layout.addWidget(self.filter_project_combo)
        filter_layout.addWidget(QLabel("Задача:"))
        filter_layout.addWidget(self.filter_task_combo)

        self.apply_filter_btn = QPushButton("Применить фильтр")
        self.apply_filter_btn.clicked.connect(self.update_stats_table)
        filter_layout.addWidget(self.apply_filter_btn)

        stats_layout.addWidget(filter_widget)

        # Общее время
        self.total_time_label = QLabel("Общее время: 00:00:00")
        self.total_time_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.total_time_label)

        # Таблица
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(6)
        stats_layout.addWidget(self.stats_table)

        self.tabs.addTab(stats_tab, "Статистика")

        # Заполняем фильтры и обновляем таблицу
        self.update_filter_combos()
        self.update_stats_table()

    def update_filter_combos(self):
        # Сохраняем текущие выбранные значения
        current_project = self.filter_project_combo.currentData()
        current_task = self.filter_task_combo.currentData()

        # Обновляем комбобокс проектов
        self.filter_project_combo.clear()
        self.filter_project_combo.addItem("Все проекты", None)

        projects = self.db.get_projects()
        for project in projects:
            self.filter_project_combo.addItem(project.name, project.id)

        # Восстанавливаем выбор проекта
        if current_project:
            index = self.filter_project_combo.findData(current_project)
            if index >= 0:
                self.filter_project_combo.setCurrentIndex(index)

        # Обновляем комбобокс задач
        self.update_filter_task_combo(current_task)

    def update_filter_task_combo(self, current_task=None):
        self.filter_task_combo.clear()
        self.filter_task_combo.addItem("Все задачи", None)

        project_id = self.filter_project_combo.currentData()
        if project_id:
            tasks = self.db.get_tasks_for_project(project_id)
            for task in tasks:
                self.filter_task_combo.addItem(task.name, task.id)

        if current_task:
            index = self.filter_task_combo.findData(current_task)
            if index >= 0:
                self.filter_task_combo.setCurrentIndex(index)

    def setup_timers(self):
        # Таймер для обновления отображения
        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(1000)

        # Таймер для проверки времени работы
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_work_time)
        self.check_timer.start(self.settings.check_interval * 1000)  # Используем настройки

    def update_projects_combo(self):
        self.project_combo.clear()
        projects = self.db.get_projects()
        for project in projects:
            self.project_combo.addItem(project.name, project.id)

        # Автоматически обновляем задачи
        self.update_tasks_combo()

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

    def update_display(self):
        elapsed = self.timer.get_elapsed_time()
        self.timer_label.setText(self.timer.format_time(elapsed))

    def check_work_time(self):
        if self.timer.is_running:
            # Приостанавливаем таймер перед показом сообщения
            was_running = self.timer.is_running
            self.timer.pause()

            # Воспроизводим звук, если включено
            if self.settings.enable_sound:
                QSound.play("alert.wav")

            reply = QMessageBox.question(
                self, 'Подтверждение',
                f"Вы работали над задачей последние {self.settings.check_interval // 60} минут?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes)

            if reply == QMessageBox.Yes:
                if was_running:
                    self.timer.start()  # Продолжаем работу
                self.check_timer.start(self.settings.check_interval * 1000)
            else:
                self.timer.reset()  # Сбрасываем таймер

    def start_timer(self):
        if self.task_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите задачу!")
            return

        self.current_task_id = self.task_combo.currentData()
        self.timer.start()
        # Перезапускаем таймер проверки с текущими настройками
        self.check_timer.stop()
        self.check_timer.start(self.settings.check_interval * 1000)

    def pause_timer(self):
        if self.timer.is_running:
            self.timer.pause()
        else:
            QMessageBox.information(self, "Инфо", "Таймер уже на паузе")

    def reset_timer(self):
        if self.timer.get_elapsed_time() > 0:
            reply = QMessageBox.question(
                self, "Подтверждение",
                "Сбросить таймер без сохранения?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.timer.reset()
        else:
            self.timer.reset()
        self.update_display()

    def stop_timer(self):
        if not self.timer.is_running and self.timer.get_elapsed_time() == 0:
            return

        elapsed = self.timer.get_elapsed_time()
        if elapsed > 0:  # Если есть что сохранять
            reply = QMessageBox.question(
                self, 'Сохранение времени',
                f"Сохранить {self.timer.format_time(elapsed)} работы?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes)

            if reply == QMessageBox.Yes:
                self.save_time_record(elapsed)

        self.timer.reset()
        self.update_display()

    def save_time_record(self, elapsed_seconds: int):
        try:
            if not self.current_task_id:
                QMessageBox.warning(self, "Ошибка", "Не выбрана задача!")
                return

            # Получаем текущее время
            end_time = datetime.now()
            # Вычисляем время начала (текущее время минус прошедшие секунды)
            start_time = end_time - timedelta(seconds=elapsed_seconds)

            # Сохраняем в БД в правильном формате
            self.db.add_time_record(
                task_id=self.current_task_id,
                start_time=start_time,  # Передаем объект datetime напрямую
                end_time=end_time,  # Передаем объект datetime напрямую
                duration_seconds=elapsed_seconds,
                was_productive=True
            )
            self.update_stats_table()
            QMessageBox.information(self, "Сохранено", "Время работы сохранено!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить время: {str(e)}")
            print(f"Ошибка сохранения: {e}")

    def on_timer_end(self, elapsed_seconds: int):
        reply = QMessageBox.question(
            self, 'Подтверждение',
            "Вы работали над задачей?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.save_time_record(elapsed_seconds)

        self.timer.reset()

    def update_stats_table(self):
        try:
            project_id = self.filter_project_combo.currentData()
            task_id = self.filter_task_combo.currentData()

            # Получаем данные с фильтрацией
            cursor = self.db.conn.cursor()
            query = '''
            SELECT tr.id, p.name AS project_name, t.name AS task_name, 
                   tr.duration_seconds, tr.start_time, tr.was_productive
            FROM time_records tr
            JOIN tasks t ON tr.task_id = t.id
            JOIN projects p ON t.project_id = p.id
            WHERE 1=1
            '''
            params = []

            if project_id:
                query += ' AND p.id = ?'
                params.append(project_id)
            if task_id:
                query += ' AND t.id = ?'
                params.append(task_id)

            query += ' ORDER BY tr.start_time DESC'

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Обновляем таблицу
            self.stats_table.setRowCount(0)
            self.stats_table.setColumnCount(6)
            self.stats_table.setHorizontalHeaderLabels(
                ["Проект", "Задача", "Время", "Дата", "Продуктивно", "Действия"])

            total_seconds = 0

            for row_idx, row in enumerate(rows):
                self.stats_table.insertRow(row_idx)

                project_item = QTableWidgetItem(row[1])
                task_item = QTableWidgetItem(row[2])

                # Форматируем время
                hours, remainder = divmod(row[3], 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                time_item = QTableWidgetItem(time_str)

                # Суммируем общее время
                total_seconds += row[3]

                date_item = QTableWidgetItem(row[4])
                productive_item = QTableWidgetItem("Да" if row[5] else "Нет")

                self.stats_table.setItem(row_idx, 0, project_item)
                self.stats_table.setItem(row_idx, 1, task_item)
                self.stats_table.setItem(row_idx, 2, time_item)
                self.stats_table.setItem(row_idx, 3, date_item)
                self.stats_table.setItem(row_idx, 4, productive_item)

                # Кнопка удаления
                btn = QPushButton("Удалить")
                btn.clicked.connect(lambda _, r=row_idx: self.delete_time_record(r))
                self.stats_table.setCellWidget(row_idx, 5, btn)

            # Обновляем общее время
            total_hours, remainder = divmod(total_seconds, 3600)
            total_minutes, total_seconds = divmod(remainder, 60)
            self.total_time_label.setText(
                f"Общее время: {total_hours:02d}:{total_minutes:02d}:{total_seconds:02d}")

            self.stats_table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить статистику: {str(e)}")

    def delete_time_record(self, row):
        # Получаем ID записи из таблицы
        record_id = self.stats_table.item(row, 0).data(Qt.UserRole)

        # Если ID не установлен, попробуем получить его из базы данных
        if not record_id:
            project_name = self.stats_table.item(row, 0).text()
            task_name = self.stats_table.item(row, 1).text()
            time_str = self.stats_table.item(row, 2).text()

            # Найдем запись в базе данных
            cursor = self.db.conn.cursor()
            cursor.execute('''
            SELECT tr.id FROM time_records tr
            JOIN tasks t ON tr.task_id = t.id
            JOIN projects p ON t.project_id = p.id
            WHERE p.name = ? AND t.name = ? AND tr.duration_seconds = ?
            ''', (project_name, task_name, self._time_str_to_seconds(time_str)))

            result = cursor.fetchone()
            if result:
                record_id = result[0]

        if record_id:
            reply = QMessageBox.question(
                self, 'Подтверждение',
                "Удалить запись времени?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)

            if reply == QMessageBox.Yes:
                if self.db.delete_time_record(record_id):
                    self.update_stats_table()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить запись")

    def _time_str_to_seconds(self, time_str):
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s

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
        try:
            dialog = self.ProjectDialog(self)  # Используем self.ProjectDialog
            if dialog.exec_() == QDialog.Accepted:
                name = dialog.get_name()
                if name:  # Проверяем, что имя не пустое
                    self.db.add_project(name)
                    self.update_projects_combo()
        except Exception as e:
            print(f"Ошибка при создании проекта: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать проект: {str(e)}")

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
        try:
            # Проверяем, что выбран проект
            if not self.project_combo.currentData():
                QMessageBox.warning(self, "Ошибка", "Сначала выберите проект!")
                return

            # Создаем и показываем диалог
            dialog = self.TaskDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                name = dialog.get_name()
                if name:  # Проверяем, что имя не пустое
                    project_id = self.project_combo.currentData()
                    # Добавляем задержку для теста (можно убрать потом)
                    QApplication.processEvents()
                    self.db.add_task(project_id, name)
                    self.update_tasks_combo()
        except Exception as e:
            print(f"Ошибка при создании задачи: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать задачу:\n{str(e)}")

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

        # Блокируем кнопки если нет проектов
        has_projects = len(projects) > 0
        self.edit_project_btn.setEnabled(has_projects)
        self.del_project_btn.setEnabled(has_projects)
        self.add_task_btn.setEnabled(has_projects)
