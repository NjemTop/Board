import multiprocessing
import os
import threading
import subprocess
import logging
from telegram_bot import start_telegram_bot

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')

# Создание объекта логгера для ошибок и критических событий
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler('app-errors.log')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M'))
error_logger.addHandler(error_handler)

# Создание объекта логгера для информационных сообщений
info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)
info_handler = logging.FileHandler('app-info.log')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M'))
info_logger.addHandler(info_handler)

# Функция запуска ВЕБ-СЕРВЕРА для прослушивания вебхуков. Алерты.
def start_socket_server():
    """Функция запуска ВЭБ-СЕРВЕРА в паралельной сессии"""
    script_path = os.path.abspath(os.path.dirname(__file__))
    subprocess.Popen(['python', os.path.join(script_path, 'socket_server.py')])

# запуск двух функций (запуск скрипта ВЭБ-СЕРВЕРА и запуск скрипта телебота)
if __name__ == '__main__':
    try:
        p1 = multiprocessing.Process(target=start_socket_server)
        # Здесь мы используем threading.Thread для запуска функции start_telegram_bot в отдельном потоке, который не блокирует выполнение остального кода.
        p2 = threading.Thread(target=start_telegram_bot)
        p1.start()
        p2.start()
        p1.join()
        p2.join()
        p2.join()
    except Exception as e:
        error_logger.error(str(e))
    else:
        info_logger.info("The program has finished running without errors.")
        logging.warning('This is a warning message')
        logging.critical('This is a critical message')
