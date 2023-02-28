import multiprocessing
import os
import threading
import subprocess
import logging
from telegram_bot import start_telegram_bot
from web_server import run_server

if __name__ == '__main__':
    # В блоке if __name__ == '__main__' добавляем freeze_support() для Windows
    if os.name == 'nt':
        multiprocessing.freeze_support()
        
    # Настройка логирования
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')

    # Создание объекта логгера для ошибок и критических событий
    error_logger = logging.getLogger('error_logger')
    error_logger.setLevel(logging.ERROR)
    # создаем обработчик, который будет записывать ошибки в файл app-error.log
    error_handler = logging.FileHandler('./logs/app-error.log')
    error_handler.setLevel(logging.ERROR)
    # создаем форматирование
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
    error_handler.setFormatter(formatter)
    # добавляем обработчик в логгер
    error_logger.addHandler(error_handler)

    # Создание объекта логгера для информационных сообщений
    info_logger = logging.getLogger('info_logger')
    info_logger.setLevel(logging.INFO)
    info_handler = logging.FileHandler('./logs/app-info.log')
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    info_logger.addHandler(info_handler)

    # запуск двух функций (запуск скрипта ВЭБ-СЕРВЕРА и запуск скрипта телебота)
    try:
        p1 = multiprocessing.Process(target=run_server)
        # Здесь мы используем threading.Thread для запуска функции start_telegram_bot в отдельном потоке, который не блокирует выполнение остального кода.
        p2 = threading.Thread(target=start_telegram_bot)
        p1.start()
        p2.start()
        p1.join()
        p2.join()
    except Exception as e:
        error_logger.error(str(e))
    else:
        info_logger.info("The program has finished running without errors.")
        logging.warning('This is a warning message')
        logging.critical('This is a critical message')
