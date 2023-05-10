import requests
import json
import logging
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
bot_error_logger = setup_logger('TeleBot', get_abs_log_path('bot-errors.log'), logging.ERROR)
bot_info_logger = setup_logger('TeleBot', get_abs_log_path('bot-info.log'), logging.INFO)

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"

# Читаем данные из файла
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    DATA = json.load(file)

# Получаем значение ключа BOT_TOKEN в TELEGRAM_SETTINGS
BOT_TOKEN = DATA['TELEGRAM_SETTINGS']['BOT_TOKEN']

class Alert():
    # ФУНКЦИЯ ОТПРАВКИ АЛЕРТА В ЧАТ
    def send_telegram_message(self, alert_chat_id, alert_text):
        """
        Отправляет сообщение в телеграм-бот.
        На себя принимает два аргумента:
        alert_chat_id - чат айди, куда мы будем отправлять сообщение,
        alert_text - текст сообщения, которое мы хотим отправить.
        """
        # Адрес для отправи сообщение напрямую через API Telegram
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        # Задаём стандартный заголовок отправки
        headers_server = {'Content-type': 'application/json'}
        # Создаём тело запроса, которое мы отправляем
        data = {
            'chat_id': alert_chat_id,
            'text': f'{alert_text}',
            'parse_mode': 'Markdown'
        }
        # Отправляем запрос через наш бот
        response = requests.post(url, headers=headers_server, data=json.dumps(data), timeout=30)
        # Добавляем логгирование для отладки
        print(response)