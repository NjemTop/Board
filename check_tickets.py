import requests
import json
import logging
import datetime
from datetime import datetime, timedelta
import pytz
import xml.etree.ElementTree as ET

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
    current_time = datetime.now()
    date_time = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    # прибавляем 3 часа
    date_time = date_time + timedelta(hours=3)
    diff = current_time - date_time
    return diff

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
        print(f"Не удалось найти chat_id для пользователя {assigned_name}.")
        check_error_logger.error("Не удалось найти chat_id для пользователя {assigned_name} %s")
    return alert_chat_id

def get_tickets():
    """Функция проверки тикетов, у которых нет ответа"""
    params = {
        'status': '2',
        'category': '1',
        'q': 'unresponded:"true"'
        #'q': 'duedate:"today"'
    }
    url = API_ENDPOINT + '/tickets/?size=1&page=1'
    # проверка на доступность сервера, если сервер недоступен, выводит ошибку
    try:
        response = requests.get(url, auth=(API_KEY, API_SECRET), headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout as error_message:
        print("Timeout error: request timed out")
        check_error_logger.error("Timeout error: request timed out: %s", error_message)
    except requests.exceptions.RequestException as error_message:
        print(f"Error occurred: {error_message}")
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
                print("Timeout error: request timed out")
                check_error_logger.error("Timeout error: request timed out: %s", error_message)
            except requests.exceptions.RequestException as error_message:
                print(f"Error occurred: {error_message}")
                check_error_logger.error("Error occurred: %s", error_message)

            data = response.json()
            for ticket_data in data.get('data'):
                ticket_id = ticket_data.get('id')
                priority_info = ticket_data.get('priority')
                priority_name = priority_info.get('name')
                user_info = ticket_data.get('user')
                contact_info = user_info.get('contact_groups')
                assigned_to = ticket_data.get('assigned_to')
                reple_client_time = ticket_data.get('last_user_reply_at')
                time_difference = get_time_diff(reple_client_time)
                if time_difference >= timedelta(hours=1):
                    print(f"Время последнего ответа клиента в тикете {time_difference}")
                    name_info = None
                    for contact in contact_info:
                        name_info = contact.get('name')
                        break
                    if isinstance(assigned_to, list):
                        for assigned in assigned_to:
                            assigned_name = assigned.get('name')
                    else:
                        if assigned_to is not None:
                            assigned_name = assigned_to.get('name')
                        else:
                            assigned_name = "Нет исполнителя"

                    ticket_message = (f'Тикет без ответа более часа: {ticket_id}\nПриоритет: {priority_name}\nНазвание клиента: {name_info}\nНазначен: {assigned_name}')

                    # Получаем chat_id для отправки сообщения
                    alert_chat_id = get_alert_chat_id(assigned_name)
                    
                    # Отправляем сообщение в телеграм-бот
                    print(ticket_message)
                    print('--'*30)
                    print(alert_chat_id)
                    print('**'*30)
                    #send_telegram_message(alert_chat_id, ticket_message)
                    check_info_logger.info('Сотруднику: %s в чат повторно отправлена информация о неотвеченном тикете: %s', assigned_name, ticket_id)

if __name__ == '__main__':
    get_tickets()