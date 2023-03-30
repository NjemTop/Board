import requests
import json

def get_happyfox_credentials(config_file):
    """Функция определения данных авторизаций в HappyFox"""
    # Открываем файл и загружаем данные
    with open(config_file, 'r', encoding='utf-8-sig') as f:
        data_config = json.load(f)
    # Извлекаем значения базового ENDPOINT, API_KEY и API_SECRET
    api_endpoint = data_config['HAPPYFOX_SETTINGS']['API_ENDPOINT']
    api_key = data_config['HAPPYFOX_SETTINGS']['API_KEY']
    api_secret = data_config['HAPPYFOX_SETTINGS']['API_SECRET']
    # Задаем заголовок
    headers = {'Content-Type': 'application/json'}
    # Возвращаем все полученные данные обратно
    return api_endpoint, api_key, api_secret, headers


def get_filtered_tickets(api_endpoint, api_key, api_secret, headers, contact_group_id, start_date, end_date):
    """
    Получает список отфильтрованных тикетов из HappyFox на основе указанной группы контактов и диапазона дат.

    :param api_endpoint: строка, URL-адрес API HappyFox
    :param api_key: строка, API-ключ для аутентификации
    :param api_secret: строка, API-секрет для аутентификации
    :param headers: словарь, содержащий заголовки запроса
    :param contact_group_id: целое число, идентификатор группы контактов, по которой нужно отфильтровать тикеты
    :param start_date: строка, начальная дата диапазона (формат "YYYY-MM-DD")
    :param end_date: строка, конечная дата диапазона (формат "YYYY-MM-DD")
    """
    # Создаем URL для запроса списка тикетов
    url = f"{api_endpoint}/tickets/"
    # Задаем параметры для запроса, включая фильтр по датам и номер страницы
    params = {
        'q': f'last-modified-on-or-after:"{start_date}" last-modified-on-or-before:"{end_date}"',
        'page': 1,
        'size': 50
    }

    # Инициализируем список отфильтрованных тикетов и переменную для отслеживания наличия следующих страниц
    filtered_tickets = []
    has_more_pages = True

    # Цикл выполняется, пока есть следующие страницы с тикетами
    while has_more_pages:
        # Отправляем запрос на получение списка тикетов с заданными параметрами
        response = requests.get(url, params=params, auth=(api_key, api_secret), headers=headers)

        # Если запрос выполнен успешно, обрабатываем результаты
        if response.status_code == 200:
            data = response.json()
            tickets = data['data']

            # Проверяем, есть ли еще страницы с тикетами (если количество тикетов на странице равно максимально возможному)
            has_more_pages = data['page_info']['count'] >= 50

            # Перебираем тикеты и проверяем, принадлежат ли они указанной контактной группе
            for ticket in tickets:
                if 'user' in ticket and ticket['user'] is not None:
                    user = ticket['user']
                    if 'contact_groups' in user:
                        contact_groups = user['contact_groups']
                        for contact_group in contact_groups:
                            if contact_group['id'] == contact_group_id:
                                # Если тикет принадлежит контактной группе, добавляем его в список отфильтрованных тикетов
                                filtered_tickets.append(ticket)
                                break

            # Если есть следующая страница, увеличиваем номер страницы для следующего запроса
            if has_more_pages:
                params['page'] += 1
        else:
            print('Error:', response.status_code)
            break

    # Возвращаем список отфильтрованных тикетов
    return filtered_tickets
