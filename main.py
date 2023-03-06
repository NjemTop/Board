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
app_info_handler = logging.FileHandler('app-info.log')
app_info_handler.setLevel(logging.INFO)
app_info_handler.setFormatter(formatter)
app_info_logger.addHandler(app_info_handler)

# Функция запуска ВЕБ-СЕРВЕРА для прослушивания вебхуков. Алерты.
def start_socket_server():
    """Функция запуска ВЭБ-СЕРВЕРА в паралельной сессии"""
    script_path = os.path.abspath(os.path.dirname(__file__))
    subprocess.Popen(['python3.10', os.path.join(script_path, 'web_server.py')])

# запуск двух функций (запуск скрипта ВЭБ-СЕРВЕРА и запуск скрипта телебота)
if __name__ == '__main__':
    try:
        p1 = multiprocessing.Process(target=start_socket_server)
        # Здесь мы используем threading.Thread для запуска функции start_telegram_bot в отдельном потоке, который не блокирует выполнение остального кода.
        p2 = threading.Thread(target=start_telegram_bot)
        p1.start()
        info_logger.info("Вэб-сервер запущен")
        p2.start()
        info_logger.info("Телебот запущен")
        p1.join()
        p2.join()
        p2.join()
    except requests.exceptions.ConnectionError as error_message:
        error_logger.error("Error in Telegram bot: %s", error_message)
    except telegram.error.TelegramError as error_message:
        error_logger.error("Error in Telegram bot: %s", error_message)
    except Exception as error_message:
        error_logger.error(str(error_message))
    else:
        info_logger.info("The program has finished running without errors.")
        logging.warning('This is a warning message')
        logging.critical('This is a critical message')