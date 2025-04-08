import json
import os


class Settings:
    def __init__(self):
        self.check_interval = 300  # 5 минут по умолчанию (в секундах)
        self.enable_sound = True
        self.loop_sound = False  # Новая настройка
        self.load()

    def save(self):
        with open('settings.json', 'w') as f:
            json.dump({
                'check_interval': self.check_interval,
                'enable_sound': self.enable_sound,
                'loop_sound': self.loop_sound  # Добавляем новую настройку
            }, f)

    def load(self):
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    data = json.load(f)
                    # Убедимся, что значения имеют правильный тип
                    self.check_interval = int(data.get('check_interval', 300))
                    self.enable_sound = bool(data.get('enable_sound', True))
                    self.loop_sound = bool(data.get('loop_sound', False))
            else:
                self.save()
        except Exception as e:
            print(f"Ошибка загрузки настроек: {repr(e)}")
            # Установим значения по умолчанию
            self.check_interval = 300
            self.enable_sound = True
            self.loop_sound = False
            self.save()