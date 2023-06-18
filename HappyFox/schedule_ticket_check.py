import schedule
import logging
import datetime
import time
import os
from HappyFox.happyfox_class import HappyFoxConnector
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
check_error_logger = setup_logger('Check_Ticket_Error', get_abs_log_path('check_ticket-errors.log'), logging.ERROR)
check_info_logger = setup_logger('Check_Ticket_Info', get_abs_log_path('check_ticket-info.log'), logging.INFO)

# Получаем абсолютный путь до файла schedule_ticket_check.py
current_file_path = os.path.abspath(os.path.dirname(__file__))
# Получаем абсолютный путь до корневой папки проекта
project_root = os.path.dirname(current_file_path)
# Формируем абсолютный путь до файла конфигурации
config_file_path = os.path.join(project_root, 'Main.config')

# Создадим объект класса HappyFoxConnector с передачей пути к файлу конфигурации
happyfox = HappyFoxConnector(config_file_path)

# Создадим задачу на отправку алертов в чат
schedule.every().day.at("10:25").do(happyfox.get_tickets)
check_info_logger.info('Задача на отправку алертов по 3х дневным простоям создана на 10:25')

def start_check_tickets():
    while True:
        # Получаем текущую дату и время
        now = datetime.datetime.now()
        # Проверяем, является ли текущий день недели будним днём (пн-пт)
        if now.weekday() < 5:
            # Запускаем отложенные задачи
            schedule.run_pending()
        # Ждём 1 секунду перед проверкой снова
        time.sleep(1)
