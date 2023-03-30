import datetime
import logging
import xml.etree.ElementTree as ET
from log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
check_error_logger = setup_logger('Check_Ticket_Error', get_abs_log_path('check_ticket-errors.log'), logging.ERROR)
check_info_logger = setup_logger('Check_Ticket_Info', get_abs_log_path('check_ticket-info.log'), logging.INFO)

class TicketUtils:
    @staticmethod
    def get_time_diff(date_str):
        """Функция подсчёта времени с последнего ответа клиента"""
        current_time = datetime.datetime.now()
        date_time = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=3)

        # Определяем день недели
        day_of_week = date_time.weekday()

        # Смещаем дату назад на количество дней, равное количеству выходных
        days_to_subtract = 0
        if day_of_week == 5:  # суббота
            days_to_subtract = 1
        elif day_of_week == 6:  # воскресенье
            days_to_subtract = 2

        # Вычисляем время между датами, исключая выходные
        business_days = 0
        elapsed_days = (current_time - date_time).days
        for day in range(1, elapsed_days+1):
            d = date_time + datetime.timedelta(days=day)
            if d.weekday() not in (5, 6):
                business_days += 1
        elapsed_days = business_days - days_to_subtract
        diff = datetime.timedelta(days=elapsed_days, seconds=(current_time - date_time).seconds)

        return diff

    @staticmethod
    def get_assigned_name(assigned_to):
        if isinstance(assigned_to, list):
            for assigned in assigned_to:
                assigned_name = assigned.get('name')
                break
        else:
            if assigned_to is not None:
                assigned_name = assigned_to.get('name')
            else:
                assigned_name = "Нет исполнителя"
        return assigned_name

    @staticmethod
    def get_name_info(contact_info):
        name_info = None
        for contact in contact_info:
            name_info = contact.get('name')
            break
        return name_info

    @staticmethod
    def get_contact_name(contact_groups):
        """Функция для получения имени контактной группы"""
        name_info = None
        for contact in contact_groups:
            name_info = contact.get('name')
            break
        return name_info

    @staticmethod
    def get_alert_chat_id(assigned_name):
        """"Функция получения chat_id для отправки сообщения"""
        # Разбор XML-файла и получение корневого элемента
        tree = ET.parse('data.xml')
        root = tree.getroot()
        # Находим все элементы header_footer внутри элемента user
        header_footer_elements = root.findall('.//user/header_footer')
        # Задаем начальное значение alert_chat_id
        alert_chat_id = None
        # Проходим циклом по всем найденным элементам header_footer
        for header_footer in header_footer_elements:
            # Сравниваем значение элемента name с assignee_name
            if header_footer.find('name').text == assigned_name:
                # Если значения совпадают, сохраняем значение элемента chat_id в alert_chat_id
                alert_chat_id = header_footer.find('chat_id').text
                break  # Выходим из цикла, т.к. нужный элемент уже найден

        # Если alert_chat_id не был найден, выводим ошибку
        if alert_chat_id is None:
            check_error_logger.error("Не удалось найти chat_id для пользователя {assigned_name} %s")
        return alert_chat_id
