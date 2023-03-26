import requests
import json
import logging

logging.basicConfig(level=logging.DEBUG, filename='web_server.log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
# Создание объекта логгера для ошибок и критических событий
web_error_logger = logging.getLogger('WebError')
web_error_logger.setLevel(logging.ERROR)
web_error_handler = logging.FileHandler('./logs/web-errors.log')
web_error_handler.setLevel(logging.ERROR)
web_error_handler.setFormatter(formatter)
web_error_logger.addHandler(web_error_handler)

# Создание объекта логгера для информационных сообщений
web_info_logger = logging.getLogger('WebInfo')
web_info_logger.setLevel(logging.INFO)
web_info_handler = logging.FileHandler('./logs/web-info.log')
web_info_handler.setLevel(logging.INFO)
web_info_handler.setFormatter(formatter)
web_info_logger.addHandler(web_info_handler)

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
        # Добавляем логгирование для отладки
        web_info_logger.info("send_telegram_message function was called with parameters: alert_chat_id=%s, alert_text=%s", alert_chat_id, alert_text)
        web_info_logger.info("Response from Telegram API: %s", response)