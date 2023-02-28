import requests
from telegram_bot import send_telegram_message

TICKET_URL = 'https://boardmaps.happyfox.com/api/1.1/json/tickets/'
API_KEY = '45357d176a5f4e25b740aebae58f189c'
API_SECRET = '3b9e5c6cc6f34802ad5ae82bafdab3bd'
HEADERS = {'Content-Type': 'application/json'}


def get_tickets():
    """Функция проверки тикетов, у которых нет ответа"""
    params = {
        'status': '2',
        'category': '1',
        # 'unresponded': 'true',
        'q': 'unresponded:"true"',
    }
    url = TICKET_URL + '?size=1&page=1'
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
                url = TICKET_URL + f'?size=1&page={page + 1}'
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

                    ticket_message = (f'Ticket ID: {ticket_id}, Priority: {priority_name}, Contact Group Name: {name_info}, assignee: {assigned_name}')
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

