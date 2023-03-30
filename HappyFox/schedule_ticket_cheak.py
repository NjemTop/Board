import schedule
import logging
from HappyFox.happyfox_class import HappyFoxConnector

# Создание объекта логгера для ошибок и критических событий
check_error_logger = logging.getLogger('Check_Ticket_Error')
check_error_logger.setLevel(logging.ERROR)
check_error_handler = logging.FileHandler('./logs/check_ticket-errors.log')
check_error_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
check_error_handler.setFormatter(formatter)
check_error_logger.addHandler(check_error_handler)

# Создание объекта логгера для информационных сообщений
check_info_logger = logging.getLogger('Check_Ticket_Info')
check_info_logger.setLevel(logging.INFO)
check_info_handler = logging.FileHandler('./logs/check_ticket-info.log')
check_info_handler.setLevel(logging.INFO)
check_info_handler.setFormatter(formatter)
check_info_logger.addHandler(check_info_handler)

# Создадим объект класса HappyFoxConnector
HappyFox = HappyFoxConnector()

# Создадим задачу на отправку алертов в чат
schedule.every().day.at("10:25").do(HappyFoxConnector.get_tickets)
check_info_logger.info('Задача на отправку алертов по 3х дневным простоям создана')

if __name__ == '__main__':
    HappyFoxConnector.get_tickets()
