from dataclasses import dataclass
from datetime import datetime

@dataclass
class Project:
    id: int
    name: str

@dataclass
class Task:
    id: int
    project_id: int
    name: str
#stable
@dataclass
class TimeRecord:
    id: int
    task_id: int
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    was_productive: bool
