import schedule
import logging
import datetime
import time
import os
from HappyFox.happyfox_class import HappyFoxConnector

# Создание объекта логгера для ошибок и критических событий
check_error_logger = logging.getLogger('Check_Ticket_Error')
check_error_logger.setLevel(logging.ERROR)
check_error_handler = logging.FileHandler('../logs/check_ticket-errors.log')
check_error_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
check_error_handler.setFormatter(formatter)
check_error_logger.addHandler(check_error_handler)

# Создание объекта логгера для информационных сообщений
check_info_logger = logging.getLogger('Check_Ticket_Info')
check_info_logger.setLevel(logging.INFO)
check_info_handler = logging.FileHandler('../logs/check_ticket-info.log')
check_info_handler.setLevel(logging.INFO)
check_info_handler.setFormatter(formatter)
check_info_logger.addHandler(check_info_handler)

# Получаем абсолютный путь до файла schedule_ticket_check.py
current_file_path = os.path.abspath(os.path.dirname(__file__))
# Получаем абсолютный путь до корневой папки проекта
project_root = os.path.dirname(current_file_path)
# Формируем абсолютный путь до файла конфигурации
config_file_path = os.path.join(project_root, 'Main.config')

# Создадим объект класса HappyFoxConnector с передачей пути к файлу конфигурации
happyfox = HappyFoxConnector(config_file_path)

# Создадим задачу на отправку алертов в чат
schedule.every().day.at("10:28").do(happyfox.get_tickets)
check_info_logger.info('Задача на отправку алертов по 3х дневным простоям создана')

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
