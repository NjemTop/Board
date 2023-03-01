import requests
import json
import logging
import xml.etree.ElementTree as ET

# Создание объекта логгера для ошибок и критических событий
error_logger = logging.getLogger(__name__)
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler('check_ticket-errors.log')
error_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
error_handler.setFormatter(formatter)
error_logger.addHandler(error_handler)

# Создание объекта логгера для информационных сообщений
info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)
info_handler = logging.FileHandler('check_ticket-info.log')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)
info_logger.addHandler(info_handler)

### Авторизация в HappyFox
# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"
# открываем файл и загружаем данные
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
# извлекаем значения API_KEY и API_SECRET
API_ENDPOINT = data['HAPPYFOX_SETTINGS']['API_ENDPOINT']
API_KEY = data['HAPPYFOX_SETTINGS']['API_KEY']
API_SECRET = data['HAPPYFOX_SETTINGS']['API_SECRET']
# сохраняем значения в переменную auth
HEADERS = {'Content-Type': 'application/json'}

def get_tickets():
    """Функция проверки тикетов, у которых нет ответа"""
    params = {
        #'status': '2',
        'category': '1',
        # 'unresponded': 'true',
        'q': 'duedate:"today"',
    }
    url = API_ENDPOINT + '/tickets/?size=1&page=1'
    # проверка на доступность сервера, если сервер недоступен, выводит ошибку
    try:
        response = requests.get(url, auth=(
            API_KEY, API_SECRET), headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        response.raise_for_status()
        data = response.json()
        page_info = data.get('page_info')
        last_index = page_info.get('last_index')
        if last_index == 0:
            print('No tickets')
        else:
            for page in range(last_index):
                url = API_ENDPOINT + f'/tickets/?size=1&page={page + 1}'
                # проверка на доступность сервера, если сервер недоступен, выводит ошибку
                try:
                    response = requests.get(url, auth=(
                        API_KEY, API_SECRET), headers=HEADERS, params=params, timeout=10)
                    response.raise_for_status()
                    response.raise_for_status()
                    data = response.json()
                    for ticket_data in data.get('data'):
                        ticket_id = ticket_data.get('id')
                        priority_info = ticket_data.get('priority')
                        priority_name = priority_info.get('name')
                        user_info = ticket_data.get('user')
                        contact_info = user_info.get('contact_groups')
                        assigned_to = ticket_data.get('assigned_to')
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

                    ticket_message = (f'Тикет с сегоднядшим due_date: {ticket_id}\nПриоритет: {priority_name}\nНазвание клиента: {name_info}\nНазначен: {assigned_name}')
                    # Разбор XML-файла и получение корневого элемента
                    tree = ET.parse('data.xml')
                    root = tree.getroot()
                    # Находим все элементы header_footer внутри элемента user
                    header_footer_elements = root.findall('.//user/header_footer')
                    # Задаем начальное значение alert_chat_id
                    alert_chat_id = None
                    # Проходим циклом по всем найденным элементам header_footer
                    for hf in header_footer_elements:
                        # Сравниваем значение элемента name с assignee_name
                        if hf.find('name').text == assigned_name:
                            # Если значения совпадают, сохраняем значение элемента chat_id в alert_chat_id
                            alert_chat_id = hf.find('chat_id').text
                            break  # Выходим из цикла, т.к. нужный элемент уже найден

                    # Если alert_chat_id не был найден, выводим ошибку
                    if alert_chat_id is None:
                        print(f"Не удалось найти chat_id для пользователя {assigned_name}.")
                        error_logger.error("Не удалось найти chat_id для пользователя {assigned_name} %s")
                    else:
                        # Отправляем сообщение в телеграм-бот
                        print(ticket_message)
                        print(alert_chat_id)
                        #send_telegram_message(alert_chat_id, ticket_message)
                    info_logger.info('Отправлена следующая информация в группу: %s', 'Тикет с сегоднядшим due_date: {ticket_id}Тема: {subject}Приоритет: {priority_name}Имя клиента: {client_name}Назначен: {assigned_name}Ссылка: {agent_ticket_url}')
                    #alert_chat_id = -1001760725213
                    #send_telegram_message(alert_chat_id, ticket_message)
                except requests.exceptions.Timeout:
                    print("Timeout error: request timed out")
                except requests.exceptions.RequestException as exception:
                    print(f"Error occurred: {exception}")
    except requests.exceptions.Timeout:
        print("Timeout error: request timed out")
    except requests.exceptions.RequestException as exception:
                    print(f"Error occurred: {exception}")

if __name__ == '__main__':
    get_tickets()