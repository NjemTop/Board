import requests
import json
from telegram_bot import send_telegram_message

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
        'status': '2',
        'category': '1',
        # 'unresponded': 'true',
        'q': 'unresponded:"true"',
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

                    ticket_message = (f'Новое сообщение в тикете: {ticket_id}\nПриоритет: {priority_name}\nНазвание клиента: {name_info}\nНазначен: {assigned_name}')
                    # Чат айди, куда отправляем алерты
                    alert_chat_id = -1001760725213
                    send_telegram_message(alert_chat_id, ticket_message)
                    print(ticket_message)
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