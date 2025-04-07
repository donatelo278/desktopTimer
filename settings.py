import json


class Settings:
    def __init__(self):
        self.check_interval = 300  # 5 минут по умолчанию (в секундах)
        self.enable_sound = True
        self.load()

    def save(self):
        with open('settings.json', 'w') as f:
            json.dump({'check_interval': self.check_interval,
                       'enable_sound': self.enable_sound}, f)

    def load(self):
        try:
            with open('settings.json', 'r') as f:
                data = json.load(f)
                self.check_interval = max(60, min(data.get('check_interval', 300), 7200))  # 1-120 минут
                self.enable_sound = bool(data.get('enable_sound', True))
        except (FileNotFoundError, json.JSONDecodeError):
            self.save()  # Создаем файл с настройками по умолчанию