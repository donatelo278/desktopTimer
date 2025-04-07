import time
from datetime import datetime
from typing import Optional, Callable
from models import TimeRecord

class Timer:
    def __init__(self, on_timer_end: Callable[[int], None]):
        self.is_running = False
        self.start_time: Optional[float] = None
        self.elapsed_time = 0
        self.on_timer_end = on_timer_end

    def start(self):
        if not self.is_running:
            self.start_time = time.time()
            self.is_running = True

    def pause(self):
        if self.is_running and self.start_time:
            self.elapsed_time += time.time() - self.start_time
            self.is_running = False

    def reset(self):
        self.is_running = False
        self.start_time = None
        self.elapsed_time = 0

    def get_elapsed_time(self) -> int:
        current_elapsed = self.elapsed_time
        if self.is_running and self.start_time:
            current_elapsed += time.time() - self.start_time
        return int(current_elapsed)

    def format_time(self, seconds: int) -> str:
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"

    def check_timer(self, check_interval_seconds: int = 300):  # 5 минут = 300 секунд
        elapsed = self.get_elapsed_time()
        if elapsed >= check_interval_seconds:
            self.pause()
            self.on_timer_end(elapsed)
            return True
        return False