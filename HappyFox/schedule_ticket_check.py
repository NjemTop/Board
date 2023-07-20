import schedule
import subprocess
import logging
import datetime
import time
import os
import holidays
from HappyFox.happyfox_class import HappyFoxConnector
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
check_error_logger = setup_logger('Check_Ticket_Error', get_abs_log_path('check_ticket-errors.log'), logging.ERROR)
check_info_logger = setup_logger('Check_Ticket_Info', get_abs_log_path('check_ticket-info.log'), logging.INFO)

# Создаем объект календаря праздников для России
ru_holidays = holidays.RU()

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
schedule.every().day.at("22:46").do(happyfox.get_open_tickets)
schedule.every().sunday.at("00:00").do(subprocess.run, ['pip', 'install', '--upgrade', 'holidays'])
check_info_logger.info('Задача на отправку алертов по 3-х дневным простоям создана на 10:25')
check_info_logger.info('Задача на отправку информации об открытых тикетах создана на 10:30')
check_info_logger.info('Задача на автоматическое обновление библиотеки holidays создана на каждое воскресенье в 00:00')

def is_business_day(date):
    if date.weekday() >= 5 or date in ru_holidays:
        return False
    return True

def start_check_tickets():
    while True:
        # Получаем текущую дату и время
        now = datetime.datetime.now()
        # Проверяем, является ли текущий день рабочим (будним)
        if is_business_day(now):
            # Запускаем отложенные задачи
            schedule.run_pending()
        # Ждём 1 секунду перед проверкой снова
        time.sleep(1)
