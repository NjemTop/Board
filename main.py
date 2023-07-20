import multiprocessing
import os
import threading
import subprocess
import logging
import requests
import telegram
from telegram_bot import start_telegram_bot
from HappyFox.schedule_ticket_check import start_check_tickets
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
app_error_logger = setup_logger('AppError', get_abs_log_path('app-errors.log'), logging.ERROR)
app_info_logger = setup_logger('AppInfo', get_abs_log_path('app-info.log'), logging.INFO)

if __name__ == '__main__':
    # Запускаем шедуллер
    try:
        p1 = threading.Thread(target=start_check_tickets)
        p1.start()
        app_info_logger.info("Планировщик задач запущен")
    except Exception as error_message:
        app_error_logger.error("Ошибка в файле 'Schedule_ticket_check': %s", error_message)
    # Запускаем телеграм бота
    try:
        p2 = threading.Thread(target=start_telegram_bot)
        p2.start()
        app_info_logger.info("Телебот запущен")
        p2.join()
    except requests.exceptions.ConnectionError as error_message:
        app_error_logger.error("Ошибка подключения к Telegram bot: %s", error_message)
    except telegram.error.TelegramError as error_message:
        app_error_logger.error("Ошибка в Telegram bot: %s", error_message)
    except Exception as error_message:
        app_error_logger.error(str(error_message))
    else:
        app_error_logger.critical('Неизветная ошибка')
