import requests
import json
import logging
import datetime
from datetime import datetime, timedelta
import schedule
import time
import datetime
import xml.etree.ElementTree as ET
from telegram_bot import send_telegram_message

# Создание объекта логгера для ошибок и критических событий
check_error_logger = logging.getLogger('Check_Ticket_Error')
check_error_logger.setLevel(logging.ERROR)
check_error_handler = logging.FileHandler('check_ticket-errors.log')
check_error_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
check_error_handler.setFormatter(formatter)
check_error_logger.addHandler(check_error_handler)

# Создание объекта логгера для информационных сообщений
check_info_logger = logging.getLogger('Check_Ticket_Info')
check_info_logger.setLevel(logging.INFO)
check_info_handler = logging.FileHandler('check_ticket-info.log')
check_info_handler.setLevel(logging.INFO)
check_info_handler.setFormatter(formatter)
check_info_logger.addHandler(check_info_handler)

### Авторизация в HappyFox
# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"
# открываем файл и загружаем данные
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
    data_config = json.load(f)
# извлекаем значения API_KEY и API_SECRET
API_ENDPOINT = data_config['HAPPYFOX_SETTINGS']['API_ENDPOINT']
API_KEY = data_config['HAPPYFOX_SETTINGS']['API_KEY']
API_SECRET = data_config['HAPPYFOX_SETTINGS']['API_SECRET']
# сохраняем значения в переменную auth
HEADERS = {'Content-Type': 'application/json'}

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

def get_name_info(contact_info):
    name_info = None
    for contact in contact_info:
        name_info = contact.get('name')
        break
    return name_info

def get_contact_name(contact_groups):
    """Функция для получения имени контактной группы"""
    name_info = None
    for contact in contact_groups:
        name_info = contact.get('name')
        break
    return name_info

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

def process_ticket(ticket_data):
    """Функция по формированию данных из тикета"""
    status = ticket_data.get('status').get('behavior')
    # Узнаём в работе ли ещё тикет
    if status == "pending":
        ticket_id = ticket_data.get('id')
        priority_info = ticket_data.get('priority')
        priority_name = priority_info.get('name')
        user_info = ticket_data.get('user')
        contact_info = user_info.get('contact_groups')
        assigned_to = ticket_data.get('assigned_to')
        # Проверяем, что значение для поля last_staff_reply_at существует
        if ticket_data.get('last_staff_reply_at'):
            reple_client_time = ticket_data.get('last_staff_reply_at')
            time_difference = get_time_diff(reple_client_time)
            # Проверяем, что в тикете нет ответа более 3х дней
            if time_difference >= timedelta(days=3):
                name_info = get_contact_name(contact_info)
                assigned_name = get_assigned_name(assigned_to)
                # print(f"Время последнего ответа клиента в тикете {time_difference}")

                ticket_message = (f'Тикет без ответа более 3 дней: {ticket_id}\nПриоритет: {priority_name}\nНазвание клиента: {name_info}\nНазначен: {assigned_name}')

                # Получаем chat_id для отправки сообщения
                alert_chat_id = get_alert_chat_id(assigned_name)
                
                # Отправляем сообщение в телеграм-бот
                # print(ticket_message)
                # print('--'*30)
                # print(alert_chat_id)
                # print('**'*30)
                send_telegram_message(alert_chat_id, ticket_message)
                check_info_logger.info('Сотруднику: %s в чат отправлена информация о 3х дневном неотвеченном тикете: %s', assigned_name, ticket_id)

def get_tickets():
    """Функция проверки тикетов, у которых нет ответа"""
    params = {
        #'status': '1,2,3',  # выбираем все статусы, кроме "Закрыт"
        #'status_neq': '4',       # Исключить закрытые статусы
        'category': '1',
        #'q': 'behavior:pending'
        #'q': 'unresponded:"true"'
        #'q': 'duedate:"today"'
    }
    url = API_ENDPOINT + '/tickets/?size=1&page=1'
    # проверка на доступность сервера, если сервер недоступен, выводит ошибку
    try:
        response = requests.get(url, auth=(API_KEY, API_SECRET), headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout as error_message:
        check_error_logger.error("Timeout error: request timed out: %s", error_message)
    except requests.exceptions.RequestException as error_message:
        check_error_logger.error("Error occurred: %s", error_message)
        
    data_res = response.json()
    page_info = data_res.get('page_info')
    last_index = page_info.get('last_index')
    if last_index == 0:
        print('No tickets')
    else:
        for page in range(last_index):
            url = API_ENDPOINT + f'/tickets/?size=1&page={page + 1}'
            # проверка на доступность сервера, если сервер недоступен, выводит ошибку
            try:
                response = requests.get(url, auth=(API_KEY, API_SECRET), headers=HEADERS, params=params, timeout=10)
                response.raise_for_status()
            except requests.exceptions.Timeout as error_message:
                check_error_logger.error("Timeout error: request timed out: %s", error_message)
            except requests.exceptions.RequestException as error_message:
                check_error_logger.error("Error occurred: %s", error_message)
            data = response.json()
            for ticket_data in data.get('data'):
                process_ticket(ticket_data)
                

# Создадим задачу на отправку алертов в чат
schedule.every().day.at("10:25").do(get_tickets)

while True:
    # Получаем текущую дату и время
    now = datetime.datetime.now()
    # Проверяем, является ли текущий день недели будним днём (пн-пт)
    if now.weekday() < 5:
        # Запускаем отложенные задачи
        schedule.run_pending()
    # Ждём 1 секунду перед проверкой снова
    time.sleep(1)

if __name__ == '__main__':
    get_tickets()