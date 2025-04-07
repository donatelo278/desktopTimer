import json


class Settings:
    def __init__(self):
        self.check_interval = 300  # 5 минут по умолчанию (в секундах)
        self.enable_sound = True

    def save(self):
        with open('settings.json', 'w') as f:
            json.dump({'check_interval': self.check_interval,
                       'enable_sound': self.enable_sound}, f)

    def load(self):
        try:
            with open('settings.json', 'r') as f:
                data = json.load(f)
                self.check_interval = data.get('check_interval', 300)
                self.enable_sound = data.get('enable_sound', True)
        except FileNotFoundError:
            self.save()  # Создаем файл с настройками по умолчанию