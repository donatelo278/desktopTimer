import sqlite3
from typing import List
from datetime import datetime
from models import Project, Task, TimeRecord


class Database:
    def __init__(self, db_path='db/timer.db'):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            UNIQUE(project_id, name)
        )''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            duration_seconds INTEGER NOT NULL,
            was_productive BOOLEAN NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )''')
        self.conn.commit()

    # Методы для работы с проектами
    def add_project(self, name: str) -> Project:
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO projects (name) VALUES (?)', (name,))
        self.conn.commit()
        return Project(id=cursor.lastrowid, name=name)

    def get_projects(self) -> List[Project]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name FROM projects')
        return [Project(id=row[0], name=row[1]) for row in cursor.fetchall()]

    def delete_project(self, project_id: int) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False

    # Методы для работы с задачами
    def add_task(self, project_id: int, name: str) -> Task:
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO tasks (project_id, name) VALUES (?, ?)', (project_id, name))
        self.conn.commit()
        return Task(id=cursor.lastrowid, project_id=project_id, name=name)

    def get_tasks_for_project(self, project_id: int) -> List[Task]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, project_id, name FROM tasks WHERE project_id = ?', (project_id,))
        return [Task(id=row[0], project_id=row[1], name=row[2]) for row in cursor.fetchall()]

    def delete_task(self, task_id: int) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False

    # Методы для работы с записями времени
    def add_time_record(self, task_id: int, start_time: datetime, end_time: datetime,
                        duration_seconds: int, was_productive: bool) -> TimeRecord:
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO time_records 
        (task_id, start_time, end_time, duration_seconds, was_productive) 
        VALUES (?, ?, ?, ?, ?)''',
                       (task_id,
                        start_time.strftime("%Y-%m-%d %H:%M:%S"),  # Форматируем дату
                        end_time.strftime("%Y-%m-%d %H:%M:%S"),  # перед сохранением
                        duration_seconds,
                        was_productive))
        self.conn.commit()
        return TimeRecord(
            id=cursor.lastrowid,
            task_id=task_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            was_productive=was_productive
        )

    def get_time_records_for_task(self, task_id: int) -> List[TimeRecord]:
        """
        Получает все записи времени для указанной задачи

        Args:
            task_id: ID задачи

        Returns:
            Список объектов TimeRecord для указанной задачи,
            отсортированный по времени начала (новые сначала)
        """
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT 
            tr.id,
            tr.task_id,
            tr.start_time,
            tr.end_time,
            tr.duration_seconds,
            tr.was_productive,
            p.name as project_name,
            t.name as task_name
        FROM time_records tr
        JOIN tasks t ON tr.task_id = t.id
        JOIN projects p ON t.project_id = p.id
        WHERE tr.task_id = ?
        ORDER BY tr.start_time DESC
        ''', (task_id,))

        records = []
        for row in cursor.fetchall():
            record = TimeRecord(
                id=row[0],
                task_id=row[1],
                start_time=datetime.fromisoformat(row[2]),
                end_time=datetime.fromisoformat(row[3]),
                duration_seconds=row[4],
                was_productive=bool(row[5]),
                project_name=row[6],
                task_name=row[7]
            )
            records.append(record)

        return records

    def get_all_time_records(self) -> List[TimeRecord]:
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT 
            tr.id, 
            tr.task_id, 
            tr.start_time, 
            tr.end_time, 
            tr.duration_seconds, 
            tr.was_productive,
            p.name as project_name,
            t.name as task_name
        FROM time_records tr
        JOIN tasks t ON tr.task_id = t.id
        JOIN projects p ON t.project_id = p.id
        ORDER BY tr.start_time DESC
        ''')

        records = []
        for row in cursor.fetchall():
            records.append(
                TimeRecord(
                    id=row[0],
                    task_id=row[1],
                    start_time=datetime.fromisoformat(row[2]),
                    end_time=datetime.fromisoformat(row[3]),
                    duration_seconds=row[4],
                    was_productive=bool(row[5]),
                    # Добавляем дополнительную информацию для удобства
                    project_name=row[6],
                    task_name=row[7]
                )
            )
        return records

    def delete_time_record(self, record_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM time_records WHERE id = ?', (record_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def update_project(self, project_id: int, new_name: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE projects SET name = ? WHERE id = ?",
            (new_name, project_id))
        self.conn.commit()
        return cursor.rowcount > 0

    def update_task(self, task_id: int, new_name: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE tasks SET name = ? WHERE id = ?",
            (new_name, task_id))
        self.conn.commit()
        return cursor.rowcount > 0