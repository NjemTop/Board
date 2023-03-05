import multiprocessing
import os
import threading
import subprocess
import logging
from concurrent.futures import ThreadPoolExecutor
from telegram_bot import start_telegram_bot
from web_server import run_server

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')

# Создание объекта логгера для ошибок и критических событий
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler('./logs/app-error.log')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M'))
error_logger.addHandler(error_handler)

# Создание объекта логгера для информационных сообщений
info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)
info_handler = logging.FileHandler('./logs/app-info.log')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M'))
info_logger.addHandler(info_handler)

# Функция запуска ВЕБ-СЕРВЕРА для прослушивания вебхуков. Алерты.
# def start_socket_server():
#     """Функция запуска ВЭБ-СЕРВЕРА в паралельной сессии"""
#     script_path = os.path.abspath(os.path.dirname(__file__))
#     subprocess.Popen(['python3.10', os.path.join(script_path, 'web_server.py')])

# запуск двух функций (запуск скрипта ВЭБ-СЕРВЕРА и запуск скрипта телебота)
if __name__ == '__main__':
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(run_server)
            executor.submit(start_telegram_bot)
    except Exception as e:
        error_logger.error(str(e))
    else:
        info_logger.info("The program has finished running without errors.")
        logging.warning('This is a warning message')
        logging.critical('This is a critical message')