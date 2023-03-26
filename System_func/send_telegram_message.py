import requests
import json

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"

# Читаем данные из файла
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    DATA = json.load(file)

# Получаем значение ключа BOT_TOKEN в TELEGRAM_SETTINGS
BOT_TOKEN = DATA['TELEGRAM_SETTINGS']['BOT_TOKEN']

class Alert():
    # ФУНКЦИЯ ОТПРАВКИ АЛЕРТА В ЧАТ
    def send_telegram_message(alert_chat_id, alert_text):
        """Отправляет сообщение в телеграм-бот"""
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        headers_server = {'Content-type': 'application/json'}
        data = {'chat_id': alert_chat_id, 'text': f'{alert_text}'}
        response = requests.post(url, headers=headers_server, data=json.dumps(data), timeout=30)
        print(response)