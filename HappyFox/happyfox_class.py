import requests
import json
import logging
import emoji
import holidays
import datetime
from datetime import timedelta
from System_func.send_telegram_message import Alert
from HappyFox.ticket_utils import TicketUtils
from logger.log_config import setup_logger, get_abs_log_path


# Указываем настройки логов для нашего файла с классами
hf_class_error_logger = setup_logger('HF_class_Error', get_abs_log_path('hf_class-errors.log'), logging.ERROR)
hf_class_info_logger = setup_logger('HF_class_Info', get_abs_log_path('hf_class-info.log'), logging.INFO)

# Создаем объект класса Alert
alert = Alert()


def is_business_day(date):
    ru_holidays = holidays.RU()
    if date.weekday() >= 5 or date in ru_holidays:
        return False
    return True


class HappyFoxConnector:
    def __init__(self, config_file):
        try:
            with open(config_file, 'r', encoding='utf-8-sig') as f:
                data_config = json.load(f)
        except FileNotFoundError as error_message:
            hf_class_error_logger.error(f"Конфигурационный файл не найден: {config_file}. Error: {error_message}")
            raise
        except json.JSONDecodeError as error_message:
            hf_class_error_logger.error(f"Ошибка декодирования JSON файла из конфигурации: {config_file}. Error: {error_message}")
            raise
        self.api_endpoint = data_config['HAPPYFOX_SETTINGS']['API_ENDPOINT']
        self.api_key = data_config['HAPPYFOX_SETTINGS']['API_KEY']
        self.api_secret = data_config['HAPPYFOX_SETTINGS']['API_SECRET']
        self.headers = {'Content-Type': 'application/json'}


    def get_filtered_tickets(self, start_date, end_date, contact_group_id):
        """
        Функция для получения списка тикетов, отфильтрованных по заданным параметрам:
        start_date (str): начальная дата диапазона времени для фильтрации тикетов
        end_date (str): конечная дата диапазона времени для фильтрации тикетов
        contact_group_id (int): ID группы контактов для фильтрации тикетов
        """
        url = f"{self.api_endpoint}/tickets/"
        page = 1
        all_tickets = []

        while True:
            params = {
                'q': f'last-staff-replied-on-or-after:"{start_date}" last-staff-replied-on-or-before:"{end_date}"',
                'page': page,
                'size': 50
            }

            try:
                response = requests.get(url, params=params, auth=(self.api_key, self.api_secret), headers=self.headers, timeout=10)
                response.raise_for_status()
            except requests.exceptions.HTTPError as error_message:
                hf_class_error_logger.error(f"Ошиба HTTP запроса: {error_message}")
                break
            except requests.exceptions.Timeout as error_message:
                hf_class_error_logger.error(f"Ошибка тайм-аута: {error_message}")
                break
            except requests.exceptions.RequestException as error_message:
                hf_class_error_logger.error(f"Общая ошибка: {error_message}")
                break

            data = response.json()
            tickets = data['data']

            for ticket in tickets:
                if 'user' in ticket and ticket['user'] is not None:
                    user = ticket['user']
                    if 'contact_groups' in user:
                        contact_groups = user['contact_groups']
                        if any(contact_group['id'] == contact_group_id for contact_group in contact_groups):
                            all_tickets.append(ticket)

            if data['page_info']['count'] < 50:
                break
            page += 1
        hf_class_info_logger.info('Вывод тикеты отправлены')
        return all_tickets


    def get_tickets(self):
        """Функция проверки тикетов, у которых нет ответа"""
        hf_class_info_logger.info('Задача запущена')
        params = {
            'category': '1',
            'status': '_pending',
        }
        url = self.api_endpoint + '/tickets/?size=1&page=1'
        try:
            response = requests.get(url, auth=(self.api_key, self.api_secret), headers=self.headers, params=params, timeout=10)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as error_message:
                hf_class_error_logger.error("Ошибка HTTP запроса: %s", error_message)
                return
        except requests.exceptions.Timeout as error_message:
            hf_class_error_logger.error("Ошибка тайм-аута: %s", error_message)
        except requests.exceptions.RequestException as error_message:
            hf_class_error_logger.error("Общая ошибка: %s", error_message)
            
        data_res = response.json()
        page_info = data_res.get('page_info')
        last_index = page_info.get('last_index')
        if last_index == 0:
            print('Нет тикетов')
        else:
            for page in range(last_index):
                url = self.api_endpoint + f'/tickets/?size=1&page={page + 1}'
                # проверка на доступность сервера, если сервер недоступен, выводит ошибку
                try:
                    response = requests.get(url, auth=(self.api_key, self.api_secret), headers=self.headers, params=params, timeout=10)
                    try:
                        response.raise_for_status()
                    except requests.exceptions.HTTPError as error_message:
                        hf_class_error_logger.error("Ошибка HTTP запроса: %s", error_message)
                        return
                except requests.exceptions.Timeout as error_message:
                    hf_class_error_logger.error("Ошибка тайм-аута: %s", error_message)
                except requests.exceptions.RequestException as error_message:
                    hf_class_error_logger.error("Общая ошибка: %s", error_message)
                data = response.json()
                for ticket_data in data.get('data'):
                    self.process_ticket(ticket_data)


    def get_open_tickets(self):
        """Функция получения информации об открытых тикетах"""
        hf_class_info_logger.info('Задача запущена (информация об открытых тикетах)')
        params = {
            'category': '1',
            'status': '_pending',
        }
        url = self.api_endpoint + '/tickets/?size=1&page=1'
        try:
            response = requests.get(url, auth=(self.api_key, self.api_secret), headers=self.headers, params=params, timeout=10)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as error_message:
                hf_class_error_logger.error("Ошибка HTTP запроса: %s", error_message)
                return
        except requests.exceptions.Timeout as error_message:
            hf_class_error_logger.error("Ошибка тайм-аута: %s", error_message)
        except requests.exceptions.RequestException as error_message:
            hf_class_error_logger.error("Общая ошибка: %s", error_message)
        
        data_res = response.json()
        page_info = data_res.get('page_info')
        last_index = page_info.get('last_index')
        if last_index == 0:
            print('Нет открытых тикетов')
        else:
            for page in range(last_index):
                url = self.api_endpoint + f'/tickets/?size=1&page={page + 1}'
                # проверка на доступность сервера, если сервер недоступен, выводит ошибку
                try:
                    response = requests.get(url, auth=(self.api_key, self.api_secret), headers=self.headers, params=params, timeout=10)
                    try:
                        response.raise_for_status()
                    except requests.exceptions.HTTPError as error_message:
                        hf_class_error_logger.error("Ошибка HTTP запроса: %s", error_message)
                        return
                except requests.exceptions.Timeout as error_message:
                    hf_class_error_logger.error("Ошибка тайм-аута: %s", error_message)
                except requests.exceptions.RequestException as error_message:
                    hf_class_error_logger.error("Общая ошибка: %s", error_message)
                data = response.json()
                for ticket_data in data.get('data'):
                    self.process_open_ticket(ticket_data)


    def process_open_ticket(self, ticket_data):
        """Функция по формированию данных об открытом тикете"""
        ticket_id = ticket_data.get('id')
        subject = ticket_data.get('subject')
        contact_groups = ticket_data.get('user', {}).get('contact_groups', [])
        company = contact_groups[0].get('name', 'Компания отсутствует') if contact_groups else 'Компания отсутствует'
        status = ticket_data.get('status').get('name')
        assigned_name = ticket_data.get('assigned_to', {}).get('name', 'Нет исполнителя')

        # Получаем последнее сообщение из массива "updates"
        updates = ticket_data.get('updates', [])
        last_message = None
        last_message_time = None
        for update in reversed(updates):
            message = update.get('message')
            if message:
                text = message.get('text')
                if text:
                    last_message = text
                    last_message_time = datetime.datetime.strptime(update['timestamp'], "%Y-%m-%d %H:%M:%S")
                    break

        if last_message:
            index = None
            # Проверяем наличие фразы "С уважением" в тексте сообщения
            if 'с уважением' in last_message.lower():
                index = last_message.lower().index('с уважением')
            # Если фраза "С уважением" не найдена, ищем фразу "From: Boardmaps Customer Support"
            elif 'from: boardmaps customer support' in last_message.lower():
                index = last_message.lower().index('from: boardmaps customer support')

            if index is not None:
                # Обрезаем сообщение до найденной фразы
                last_message = last_message[:index]

        # Обрезаем сообщение до 500 символов
        truncated_message = last_message[:500] + '...' if last_message and len(last_message) > 500 else last_message

        today = datetime.date.today()
        last_message_date = last_message_time.date().strftime("%Y-%m-%d")

        # Вычисляем количество рабочих дней между текущей датой и датой последнего сообщения
        business_days = 0
        while today != last_message_date:
            if is_business_day(datetime.datetime.strptime(today, "%Y-%m-%d").date()):
                business_days += 1
            today = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        if business_days > 3:
            date_emoji = emoji.emojize(':firecracker:')
        else:
            date_emoji = emoji.emojize(':eight_o’clock:')

        ticket_info = (
            f"{emoji.emojize(':eyes:')} Тема: {subject}\n"
            f"{emoji.emojize(':department_store:')} Компания: {company}\n"
            f"{emoji.emojize(':credit_card:')} Статус: {status}\n"
            f"{emoji.emojize(':disguised_face:')} Назначен: {assigned_name}\n"
            f"{date_emoji} Дата: {last_message_time.strftime('%d-%m-%Y %H:%M')}\n"
            f"{emoji.emojize(':envelope_with_arrow:')} Сообщение:\n\n"
            f"{truncated_message}"
        )
        chat_id = "-1001742909092"

        # Отправляем сообщение в телеграм-группу
        alert.send_telegram_message(chat_id, ticket_info)
        hf_class_info_logger.info('Информация об открытом тикете отправлена в группу: %s', chat_id)


    def process_ticket(self, ticket_data):
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
                time_difference = TicketUtils.get_time_diff(reple_client_time)
                # Проверяем, что в тикете нет ответа более 3х дней
                if time_difference >= timedelta(days=3):
                    name_info = TicketUtils.get_contact_name(contact_info)
                    assigned_name = TicketUtils.get_assigned_name(assigned_to)
                    # print(f"Время последнего ответа клиента в тикете {time_difference}")

                    ticket_message = (f'Ожидание ответа клиента более 3-х дней.\nНомер тикета:: {ticket_id}\nПриоритет: {priority_name}\nНазвание клиента: {name_info}\nНазначен: {assigned_name}')

                    # Получаем chat_id для отправки сообщения
                    alert_chat_id = TicketUtils.get_alert_chat_id(assigned_name)
                    
                    # Отправляем сообщение в телеграм-бот
                    alert.send_telegram_message(alert_chat_id, ticket_message)
                    hf_class_info_logger.info('Сотруднику: %s в чат отправлена информация о 3х дневном неотвеченном тикете: %s', assigned_name, ticket_id)
