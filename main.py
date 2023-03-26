import multiprocessing
import os
import threading
import subprocess
import logging
import requests
import telegram
from telegram_bot import start_telegram_bot

# Настройка логирования
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')

# Создание объекта логгера для ошибок и критических событий
app_error_logger = logging.getLogger('AppError')
app_error_logger.setLevel(logging.ERROR)
app_error_handler = logging.FileHandler('./logs/app-error.log')
app_error_handler.setLevel(logging.ERROR)
app_error_handler.setFormatter(formatter)
app_error_logger.addHandler(app_error_handler)

# Создание объекта логгера для информационных сообщений
app_info_logger = logging.getLogger('AppInfo')
app_info_logger.setLevel(logging.INFO)
app_info_handler = logging.FileHandler('./logs/app-info.log')
app_info_handler.setLevel(logging.INFO)
app_info_handler.setFormatter(formatter)
app_info_logger.addHandler(app_info_handler)

# Функция запуска задачи по проверке 3х дневных тикетов
def start_check_tickets():
    """Функция запуска задачи по проверке 3х дневных тикетов"""
    script_path = os.path.abspath(os.path.dirname(__file__))
    subprocess.Popen(['python3.10', os.path.join(script_path, 'check_tickets.py')])

# запуск двух функций (запуск скрипта телебота)
if __name__ == '__main__':
    start_check_tickets()
    try:
        p2 = threading.Thread(target=start_telegram_bot)
        p2.start()
        app_info_logger.info("Телебот запущен")
        p2.join()
    except requests.exceptions.ConnectionError as error_message:
        app_error_logger.error("Error in Telegram bot: %s", error_message)
    except telegram.error.TelegramError as error_message:
        app_error_logger.error("Error in Telegram bot: %s", error_message)
    except Exception as error_message:
        app_error_logger.error(str(error_message))
    else:
        app_info_logger.info("The program has finished running without errors.")
        app_error_logger.warning('This is a warning message')
        app_error_logger.critical('This is a critical message')