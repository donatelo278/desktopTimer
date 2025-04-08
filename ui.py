import sys

from PyQt5.QtMultimedia import QSound
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QMessageBox, QTabWidget,
                             QTableWidget, QTableWidgetItem, QDialog, QLineEdit, QDialogButtonBox,
                             QMessageBox, QInputDialog, QAction, QCheckBox, QSpinBox, QDateEdit)
from PyQt5.QtCore import QTimer, Qt, QUrl, QDate
from models import Project, Task, TimeRecord
from database import Database
from settings import Settings
from timer_logic import Timer
from datetime import datetime, timedelta


class TimerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            QApplication.setStyle('Fusion')  # Добавьте эту строку
            self.settings = Settings()
            self.settings.load()

            # Проверка загрузки настроек
            if not hasattr(self.settings, 'loop_sound'):
                self.settings.loop_sound = False
                self.settings.save()

            self.db = Database()
            self.timer = Timer(self.on_timer_end)
            self.current_task_id = None

            # Добавьте эти строки
            self.interval_spinbox = None
            self.sound_checkbox = None

            # Сначала инициализируем кнопки управления
            self.add_project_btn = None
            self.edit_project_btn = None
            self.del_project_btn = None
            self.add_task_btn = None
            self.edit_task_btn = None
            self.del_task_btn = None

            self.setup_ui()
            self.setup_timers()
            self.setup_settings_menu()  # Добавьте эту строку

            # Инициализация звука
            self.sound_effect = QSoundEffect()
            sound_file = QUrl.fromLocalFile("audio/audio1.wav")
            if sound_file.isValid():
                self.sound_effect.setSource(sound_file)
                self.sound_effect.setVolume(0.5)  # Установим комфортную громкость
            else:
                print("Не удалось загрузить звуковой файл")
        except Exception as e:
            print(f"Ошибка инициализации: {e}")
            QMessageBox.critical(None, "Ошибка", f"Ошибка запуска: {str(e)}")
            sys.exit(1)

    def save_settings(self, dialog):
        """Сохраняет настройки и перезапускает таймер"""
        self.settings.check_interval = self.interval_spinbox.value() * 60
        self.settings.enable_sound = self.sound_checkbox.isChecked()
        self.settings.loop_sound = self.loop_sound_checkbox.isChecked()  # Сохраняем новую настройку
        self.settings.save()

        # Перезапускаем таймер проверки
        self.check_timer.stop()
        self.check_timer.start(self.settings.check_interval * 1000)

        dialog.accept()
        QMessageBox.information(self, "Сохранено", "Настройки успешно сохранены!")

    def show_settings_dialog(self):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Настройки")
            dialog.setWindowModality(Qt.WindowModal)

            layout = QVBoxLayout()

            # Настройка интервала
            interval_layout = QHBoxLayout()
            interval_label = QLabel("Интервал проверки (минут):")
            self.interval_spinbox = QSpinBox()
            self.interval_spinbox.setRange(1, 120)
            self.interval_spinbox.setValue(int(self.settings.check_interval // 60))  # Явное преобразование в int
            interval_layout.addWidget(interval_label)
            interval_layout.addWidget(self.interval_spinbox)
            layout.addLayout(interval_layout)

            # Чекбокс звука
            self.sound_checkbox = QCheckBox("Включить звук")
            # Убедимся, что значение булевое
            sound_enabled = bool(self.settings.enable_sound)
            self.sound_checkbox.setChecked(sound_enabled)
            layout.addWidget(self.sound_checkbox)

            # Чекбокс цикличного звука
            self.loop_sound_checkbox = QCheckBox("Цикличный звук")
            # Убедимся, что значение булевое
            loop_sound_enabled = bool(self.settings.loop_sound)
            self.loop_sound_checkbox.setChecked(loop_sound_enabled)
            self.loop_sound_checkbox.setEnabled(sound_enabled)  # Зависит от основного чекбокса
            layout.addWidget(self.loop_sound_checkbox)

            # Связываем чекбоксы
            self.sound_checkbox.stateChanged.connect(
                lambda state: self.loop_sound_checkbox.setEnabled(state == Qt.Checked)
            )

            # Кнопки
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(lambda: self.save_settings(dialog))
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            dialog.setLayout(layout)
            dialog.exec_()

        except Exception as e:
            print(f"Ошибка в show_settings_dialog: {repr(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть настройки: {str(e)}")

    def setup_settings_menu(self):
        print("Создание меню настроек...")  # Добавьте эту строку для отладки
        menubar = self.menuBar()
        print(f"Меню-бар: {menubar}")  # Проверка, что menubar существует
        settings_menu = menubar.addMenu('Настройки')

        settings_action = QAction('Настройки...', self)
        settings_action.triggered.connect(self.show_settings_dialog)
        settings_menu.addAction(settings_action)
        print("Меню настроек создано")  # Подтверждение создания

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

        # Фильтр по проекту
        self.filter_project_combo = QComboBox()
        self.filter_project_combo.addItem("Все проекты", None)

        # Фильтр по задаче
        self.filter_task_combo = QComboBox()
        self.filter_task_combo.addItem("Все задачи", None)

        # Фильтры по дате
        date_filter_widget = QWidget()
        date_filter_layout = QHBoxLayout(date_filter_widget)

        # Дата "от"
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_from_edit.setDate(datetime.now().date())

        # Дата "до"
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_to_edit.setDate(datetime.now().date())

        date_filter_layout.addWidget(QLabel("Дата от:"))
        date_filter_layout.addWidget(self.date_from_edit)
        date_filter_layout.addWidget(QLabel("до:"))
        date_filter_layout.addWidget(self.date_to_edit)

        # Добавляем обработчик изменения проекта
        self.filter_project_combo.currentIndexChanged.connect(
            lambda: self.update_filter_task_combo()
        )

        # Добавляем обработчики изменений фильтров
        self.filter_project_combo.currentIndexChanged.connect(self.update_stats_table)
        self.filter_task_combo.currentIndexChanged.connect(self.update_stats_table)
        self.date_from_edit.dateChanged.connect(self.update_stats_table)
        self.date_to_edit.dateChanged.connect(self.update_stats_table)

        # Собираем все фильтры
        filter_layout.addWidget(QLabel("Проект:"))
        filter_layout.addWidget(self.filter_project_combo)
        filter_layout.addWidget(QLabel("Задача:"))
        filter_layout.addWidget(self.filter_task_combo)
        filter_layout.addWidget(date_filter_widget)

        self.apply_filter_btn = QPushButton("Применить фильтр")
        self.apply_filter_btn.clicked.connect(self.update_stats_table)
        filter_layout.addWidget(self.apply_filter_btn)

        stats_layout.addWidget(filter_widget)

        # Общее время (добавили отсутствующий элемент)
        self.total_time_label = QLabel("Общее время: 00:00:00")
        self.total_time_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.total_time_label)

        # Таблица (добавили отсутствующий элемент)
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(6)
        self.stats_table.setHorizontalHeaderLabels(
            ["Проект", "Задача", "Время", "Дата", "Продуктивно", "Действия"])
        stats_layout.addWidget(self.stats_table)

        # Добавляем вкладку (это было пропущено)
        self.tabs.addTab(stats_tab, "Статистика")
        # Заполняем фильтры данными
        self.update_filter_combos()

    def update_filter_combos(self):
        # Сохраняем текущие выбранные значения
        current_project = self.filter_project_combo.currentData()
        current_task = self.filter_task_combo.currentData()

        # Блокируем сигналы, чтобы не вызывать обновление задач при заполнении проектов
        self.filter_project_combo.blockSignals(True)
        self.filter_task_combo.blockSignals(True)

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

        # Обновляем комбобокс задач для выбранного проекта
        self.update_filter_task_combo(current_task)

        # Разблокируем сигналы
        self.filter_project_combo.blockSignals(False)
        self.filter_task_combo.blockSignals(False)

        # Устанавливаем даты по умолчанию (сегодня)
        today = QDate.currentDate()
        self.date_from_edit.setDate(today)
        self.date_to_edit.setDate(today)

        print(f"Получено проектов: {len(projects)}")  # Для отладки
        for p in projects:
            print(f"Проект: {p.id} - {p.name}")

    def update_filter_task_combo(self, current_task=None):
        # Сохраняем текущий выбор
        current_task_id = current_task if current_task else self.filter_task_combo.currentData()

        self.filter_task_combo.clear()
        self.filter_task_combo.addItem("Все задачи", None)

        project_id = self.filter_project_combo.currentData()
        if project_id:
            tasks = self.db.get_tasks_for_project(project_id)
            for task in tasks:
                self.filter_task_combo.addItem(task.name, task.id)

        # Восстанавливаем выбор задачи
        if current_task_id:
            index = self.filter_task_combo.findData(current_task_id)
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
        if not self.timer.is_running:
            return

        try:
            elapsed = self.timer.get_elapsed_time()
            was_running = self.timer.is_running
            self.timer.pause()

            if self.settings.enable_sound and self.sound_effect.isLoaded():
                if self.settings.loop_sound:
                    self.sound_effect.setLoopCount(QSoundEffect.Infinite)
                self.sound_effect.play()

            reply = QMessageBox.question(
                self, 'Подтверждение',
                f"Вы работали последние {elapsed // 60} мин. {elapsed % 60} сек.?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            self.sound_effect.stop()

            if reply == QMessageBox.Yes:
                self.save_time_record(elapsed)  # Сохраняем время
                self.timer.reset()
                if was_running:  # Перезапускаем только если таймер был активен
                    self.timer.start()
            else:
                self.timer.reset()

        except Exception as e:
            print(f"Ошибка в check_work_time: {e}")
            self.timer.reset()
        finally:
            self.check_timer.start(self.settings.check_interval * 1000)

    def play_sound(self):
        """Воспроизведение звука с учетом настроек"""
        try:
            if self.settings.loop_sound:
                self.sound_effect.setLoopCount(QSoundEffect.Infinite)
            else:
                self.sound_effect.setLoopCount(1)
            self.sound_effect.play()
        except Exception as e:
            print(f"Ошибка воспроизведения звука: {e}")

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
        try:
            if not self.timer.is_running and self.timer.get_elapsed_time() == 0:
                return

            elapsed = self.timer.get_elapsed_time()
            if elapsed > 0:
                reply = QMessageBox.question(
                    self, 'Сохранение времени',
                    f"Сохранить {self.timer.format_time(elapsed)} работы?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes)

                if reply == QMessageBox.Yes:
                    if self.save_time_record(elapsed):
                        self.timer.reset()
                        self.update_display()
                    else:
                        # Если сохранение не удалось, не сбрасываем таймер
                        return
            else:
                self.timer.reset()
                self.update_display()

        except Exception as e:
            print(f"Ошибка в stop_timer: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось остановить таймер: {str(e)}")
            self.timer.reset()

    def save_time_record(self, elapsed_seconds: int):
        if not self.current_task_id or elapsed_seconds <= 0:
            QMessageBox.warning(self, "Ошибка", "Невозможно сохранить: задача не выбрана или время равно нулю")
            return False

        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(seconds=elapsed_seconds)

            # Убираем проверку на дубликаты для тестирования
            record = self.db.add_time_record(
                task_id=self.current_task_id,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=elapsed_seconds,
                was_productive=True
            )

            QMessageBox.information(self, "Сохранено",
                                    f"Запись успешно сохранена: {elapsed_seconds} секунд")
            self.update_stats_table()
            return True

        except Exception as e:
            print(f"Ошибка при сохранении записи времени: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить запись: {str(e)}")
            return False

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

            # Получаем даты из полей ввода
            date_from = self.date_from_edit.date().toPyDate()
            date_to = self.date_to_edit.date().toPyDate()

            # Корректируем date_to, чтобы включить весь день
            date_to = datetime.combine(date_to, datetime.max.time()).date()

            # Получаем данные с фильтрацией
            cursor = self.db.conn.cursor()
            query = '''
                SELECT tr.id, p.name AS project_name, t.name AS task_name, 
                       tr.duration_seconds, tr.start_time, tr.was_productive
                FROM time_records tr
                JOIN tasks t ON tr.task_id = t.id
                JOIN projects p ON t.project_id = p.id
                WHERE date(tr.start_time) BETWEEN ? AND ?
                '''
            params = [date_from.isoformat(), date_to.isoformat()]

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
                time_str = f"{hours} ч {minutes} мин {seconds} сек"
                time_item = QTableWidgetItem(time_str)

                # Форматируем дату
                try:
                    dt = datetime.fromisoformat(row[4])
                    date_str = dt.strftime("%d.%m.%Y %H:%M:%S")
                except:
                    date_str = row[4]

                date_item = QTableWidgetItem(date_str)

                # Суммируем общее время
                total_seconds += row[3]

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
