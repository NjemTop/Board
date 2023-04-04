# coding: utf-8
import json
import logging
import requests
from flask import Flask, request, jsonify
from flask import Response
from flask import render_template
import traceback
import sqlite3
import peewee
from peewee import DoesNotExist
import os
from pathlib import Path
from DataBase.model_class import Release_info, BMInfo_onClient, ClientsCard, ContactsCard, СonnectInfoCard, BMServersCard, Integration, conn
import xml.etree.ElementTree as ET
from System_func.send_telegram_message import Alert
from Web_Server.web_config import USERNAME, PASSWORD, require_basic_auth
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"

# Создаем объект класса Alert
alert = Alert()

# Путь к БД (старый, прямой формат)
db_filename = '/var/lib/sqlite/database.db'

def get_alert_chat_id(header_footer_elements, name):
    """Функция получения chat_id из конфигурационного файла"""
    try:
        for header_footer in header_footer_elements:
            if header_footer.find('name').text == name:
                return header_footer.find('chat_id').text
        return None
    except AttributeError as error_message:
        web_error_logger.error("Ошибка при обработке xml-файла: 'chat_id' не найден для пользователя %s. Ошибка: %s", name, error_message)
        return 'Не удалось найти chat_id для пользователя.', 500

def parse_json_message(message):
    """Функция парсинга JSON-строки"""
    try:
        # проверяем наличие JSON в сообщении
        if '{' not in message:
            web_error_logger.error("JSON не найден в сообщении. %s")
            return None, 'JSON не найден в сообщении.'
        # находим JSON в сообщении
        json_start = message.find('{')
        if json_start != -1:
            json_str = message[json_start:]
        else:
            web_error_logger.error("JSON не найден в сообщении. %s")
            return None, 'JSON не найден в сообщении.'
        # парсим JSON
        json_data = json.loads(json_str)
        return json_data, None
    except ValueError as error_message:
        web_error_logger.error("Не удаётся распарсить JSON в запросе. %s", error_message)
        return None, 'Не удаётся распарсить JSON в запросе.'
    
def handle_client_reply(json_data):
    """Функция обработки сообщения клиента"""
    try:
        # находим значения для ключей
        ticket_id = json_data.get("ticket_id")
        subject = json_data.get("subject")
        priority_name = json_data.get("priority_name")
        assignee_name = json_data.get("assignee_name")
        client_name = json_data['client_details']['name']
        agent_ticket_url = json_data.get("agent_ticket_url")
        # Формируем сообщение в текст отправки
        ticket_message = (f"Новое сообщение в тикете: {ticket_id}\nТема: {subject}\nИмя клиента: {client_name}\nПриоритет: {priority_name}\nНазначен: {assignee_name}\nСсылка: {agent_ticket_url}")
        try:
            # Находим все элементы header_footer внутри элемента user
            header_footer_elements = ET.parse('data.xml').getroot().findall('.//user/header_footer')
            # Задаем начальное значение alert_chat_id
            alert_chat_id = get_alert_chat_id(header_footer_elements, assignee_name)
            # Если alert_chat_id не был найден, выводим ошибку
            if alert_chat_id is None:
                web_error_logger.error("Не удалось найти 'chat_id' для пользователя %s", assignee_name)
                # Отправляем ответ о том, что приняли файлы, однако не нашли полезной информации, но приняли же (200)
                return "OK", None
        except FileNotFoundError as error_message:
            web_error_logger.error("Не удалось найти файл data.xml. Ошибка: %s", error_message)
            return None, 'Не удалось найти файл data.xml.'
        # Отправляем сообщение в телеграм-бот
        alert.send_telegram_message(alert_chat_id, ticket_message)
        web_info_logger.info('В чат: %s, направлена информация о новом сообщении в тикете: %s', assignee_name, ticket_id)
        # Отправляем ответ о том, что всё принято и всё хорошо (201)
        return "OK", None
    except ValueError as error_message:
        web_error_logger.error("Не удалось собрать информацию из запроса, который прислал HappyFox %s", error_message)
        return None, 'Не удалось собрать информацию из запроса, который прислал HappyFox.'

def handle_assignee_change(json_data):
    """Обработка изменения назначенного в тикете"""
    try:
        # находим значения для ключей
        who_change = json_data["update"]["by"]["name"]
        new_assignee_name = json_data["update"]["assignee_change"]["new"]
        ticket_id = json_data.get("ticket_id")
        subject = json_data.get("subject")
        client_name = json_data['client_details']['name']
        priority_name = json_data.get("priority_name")
        agent_ticket_url = json_data.get("agent_ticket_url")
        if who_change == new_assignee_name:
            web_info_logger.info('Сотрудник: %s, сам себе назначил тикет %s, поэтому алерт не нужен', who_change, ticket_id)
            # Отправляем ответ о том, что приняли файлы, однако не нашли полезной информации, но приняли же (200)
            return "OK", None
        # Формируем сообщение в текст отправки
        new_assignee_name_message = (f"Сотрудником: {who_change}\nИзменил назначенного в тикете: {ticket_id}\nТема: {subject}\nИмя клиента: {client_name}\nПриоритет: {priority_name}\nСсылка: {agent_ticket_url}")
        try:
            # Находим все элементы header_footer внутри элемента user
            header_footer_elements = ET.parse('data.xml').getroot().findall('.//user/header_footer')
            # Задаем начальное значение alert_chat_id
            alert_chat_id = get_alert_chat_id(header_footer_elements, new_assignee_name)
            # Если alert_chat_id не был найден, выводим ошибку
            if alert_chat_id is None:
                web_error_logger.error("Не удалось найти 'chat_id' для пользователя %s", new_assignee_name)
                # Отправляем ответ о том, что приняли файлы, однако не нашли полезной информации, но приняли же (200)
                return "OK", None
            # Отправляем сообщение в телеграм-бот
            alert.send_telegram_message(alert_chat_id, new_assignee_name_message)
            web_info_logger.info('В чат %s, отправлена информация об изменении отвественного, номер тикета: %s', new_assignee_name, ticket_id)
            # Отправляем ответ о том, что всё принято и всё хорошо (201)
            return "OK", None
        except FileNotFoundError as error_message:
            web_error_logger.error("Не удалось найти файл data.xml. Ошибка: %s", error_message)
            return None, 'Не удалось найти файл data.xml.'
    except ValueError as error_message:
        web_error_logger.error("Не удалось собрать информацию из запроса, который прислал HappyFox %s", error_message)
        return None, 'Не удалось собрать информацию из запроса, который прислал HappyFox.'

def handle_unresponded_info_60(json_data):
    """Находит информацию о "Unresponded for 60 min" в блоке массива update"""
    try:
        assignee_name = json_data.get("assignee_name")
        ticket_id = json_data.get("ticket_id")
        subject = json_data.get("subject")
        client_name = json_data['client_details']['name']
        priority_name = json_data.get("priority_name")
        agent_ticket_url = json_data.get("agent_ticket_url")
        unresponded_info = json_data.get("update", {}).get("by", {})
        if unresponded_info.get("name") == "Unresponded for 60 min":
            # Формируем сообщение в текст отправки
            ping_ticket_message = (f"Тикет без ответа час: {ticket_id}\nТема: {subject}\nИмя клиента: {client_name}\nПриоритет: {priority_name}\nНазначен: {assignee_name}\nСсылка: {agent_ticket_url}")
            try:
                # Находим все элементы header_footer внутри элемента user
                header_footer_elements = ET.parse('data.xml').getroot().findall('.//user/header_footer')
                # Задаем начальное значение alert_chat_id
                alert_chat_id = get_alert_chat_id(header_footer_elements, assignee_name)
                # Если alert_chat_id не был найден, выводим ошибку
                if alert_chat_id is None:
                    web_error_logger.error("Не удалось найти 'chat_id' для пользователя %s", assignee_name)
                    # Отправляем ответ о том, что приняли файлы, однако не нашли полезной информации, но приняли же (200)
                    return "OK", None
                # Отправляем сообщение в телеграм-бот
                alert.send_telegram_message(alert_chat_id, ping_ticket_message)
                web_info_logger.info('В чат %s, повторно отправлена информация о новом сообщении без ответа час в тикете: %s', assignee_name, ticket_id)
                # Отправляем ответ о том, что всё принято и всё хорошо (201)
                return "OK", None
            except FileNotFoundError as error_message:
                web_error_logger.error("Не удалось найти файл data.xml. Ошибка: %s", error_message)
                return None, 'Не удалось найти файл data.xml.'
    except ValueError as error_message:
        web_error_logger.error("Не удалось собрать информацию из запроса, который прислал HappyFox %s", error_message)
        return None, 'Не удалось собрать информацию из запроса, который прислал HappyFox.'
    return None, None

def handle_unresponded_info_120(json_data):
    """Находит информацию о "Unresponded for 120 min" в блоке массива update"""
    try:
        assignee_name = json_data.get("assignee_name")
        ticket_id = json_data.get("ticket_id")
        subject = json_data.get("subject")
        client_name = json_data['client_details']['name']
        priority_name = json_data.get("priority_name")
        agent_ticket_url = json_data.get("agent_ticket_url")
        unresponded_info = json_data.get("update", {}).get("by", {})
        if unresponded_info.get("name") == "Unresponded for 120 min":
            # Формируем сообщение в текст отправки
            ping_ticket_message = (f"Тикет без ответа два часа: {ticket_id}\nТема: {subject}\nИмя клиента: {client_name}\nПриоритет: {priority_name}\nНазначен: {assignee_name}\nСсылка: {agent_ticket_url}")
            try:
                # открываем файл и загружаем данные
                with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
                    data = json.load(file)
                # извлекаем значения GROUP_ALERT_NEW_TICKET из SEND_ALERT
                alert_chat_id = data['SEND_ALERT']['GROUP_ALERT_NEW_TICKET']
                # Если alert_chat_id не был найден, выводим ошибку
                if alert_chat_id is None:
                    web_error_logger.error("Не удалось найти 'chat_id' для пользователя %s", assignee_name)
                    # Отправляем ответ о том, что приняли файлы, однако не нашли полезной информации, но приняли же (200)
                    return "OK", None
                # Отправляем сообщение в телеграм-бот
                alert.send_telegram_message(alert_chat_id, ping_ticket_message)
                web_info_logger.info('В группу отправлена информация о новом сообщении без ответа %s два часа в тикете: %s', assignee_name, ticket_id)
                # Отправляем ответ о том, что всё принято и всё хорошо (201)
                return "OK", None
            except FileNotFoundError as error_message:
                web_error_logger.error("Не удалось найти файл data.xml. Ошибка: %s", error_message)
                return None, 'Не удалось найти файл data.xml.'
    except ValueError as error_message:
        web_error_logger.error("Не удалось собрать информацию из запроса, который прислал HappyFox %s", error_message)
        return None, 'Не удалось собрать информацию из запроса, который прислал HappyFox.'
    return None, None

def handle_unresponded_info_180(json_data):
    """Находит информацию о "Unresponded for 180 min" в блоке массива update"""
    try:
        assignee_name = json_data.get("assignee_name")
        ticket_id = json_data.get("ticket_id")
        subject = json_data.get("subject")
        client_name = json_data['client_details']['name']
        priority_name = json_data.get("priority_name")
        agent_ticket_url = json_data.get("agent_ticket_url")
        unresponded_info = json_data.get("update", {}).get("by", {})
        if unresponded_info.get("name") == "Unresponded for 180 min":
            # Формируем сообщение в текст отправки
            ping_ticket_message = (f"Тикет без ответа ТРИ часа: {ticket_id}\nТема: {subject}\nИмя клиента: {client_name}\nПриоритет: {priority_name}\nНазначен: {assignee_name}\nСсылка: {agent_ticket_url}")
            try:
                # открываем файл и загружаем данные
                with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
                    data = json.load(file)
                # извлекаем значения GROUP_ALERT_NEW_TICKET из SEND_ALERT
                alert_chat_id = data['SEND_ALERT']['GROUP_ALERT_NEW_TICKET']
                # Если alert_chat_id не был найден, выводим ошибку
                if alert_chat_id is None:
                    web_error_logger.error("Не удалось найти 'chat_id' для пользователя %s", assignee_name)
                    # Отправляем ответ о том, что приняли файлы, однако не нашли полезной информации, но приняли же (200)
                    return "OK", None
                # Отправляем сообщение в телеграм-бот
                alert.send_telegram_message(alert_chat_id, ping_ticket_message)
                web_info_logger.info('В группу отправлена информация о новом сообщении без ответа %s три часа в тикете: %s', assignee_name, ticket_id)
                # Отправляем ответ о том, что всё принято и всё хорошо (201)
                return "OK", None
            except FileNotFoundError as error_message:
                web_error_logger.error("Не удалось найти файл data.xml. Ошибка: %s", error_message)
                return None, 'Не удалось найти файл data.xml.'
    except ValueError as error_message:
        web_error_logger.error("Не удалось собрать информацию из запроса, который прислал HappyFox %s", error_message)
        return None, 'Не удалось собрать информацию из запроса, который прислал HappyFox.'
    return None, None

def handler_get():
        """Функция обработки вэбхуков из HappyFox"""
        ip_address = f"Request from {request.remote_addr}: {request.url}"
        user_agent = request.headers.get('User-Agent')
        user_who = f'User-Agent: {user_agent}'
        web_info_logger.info('Кто-то зашёл на сайт c IP-адреса: %s', ip_address)
        web_info_logger.info('Его данные подключения: %s', (user_who,))
        return Response('Site', mimetype='text/plain')

def handler_get_create_ticket():
        """Функция обработки GET запросов по URL"""
        ip_address = f"Request from {request.remote_addr}: {request.url}"
        user_agent = request.headers.get('User-Agent')
        user_who = f'User-Agent: {user_agent}'
        web_info_logger.info('Кто-то зашёл на сайт c IP-адреса: %s', ip_address)
        web_info_logger.info('Его данные подключения: %s', (user_who,))
        return Response('Этот URL для получения вэбхуков(создание)', mimetype='text/plain')

def handler_post_create_ticket():
        """Функция обработки создания тикета из HappyFox"""
        message = request.data.decode('utf-8')
        # парсим JSON-строку
        json_data, error = parse_json_message(message)
        if error:
            return error, 400
        # находим значения для ключей
        ticket_id = json_data.get("ticket_id")
        subject = json_data.get("subject")
        priority_name = json_data.get("priority_name")
        agent_ticket_url = json_data.get("agent_ticket_url")
        # отправляем сообщение в телеграм-бот
        ticket_message = (f"Новый тикет: {ticket_id}\nТема: {subject}\nПриоритет: {priority_name}\nСсылка: {agent_ticket_url}")
        # открываем файл и загружаем данные
        with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
            data = json.load(file)
        # извлекаем значения GROUP_ALERT_NEW_TICKET из SEND_ALERT
        alert_chat_id = data['SEND_ALERT']['GROUP_ALERT_NEW_TICKET']
        alert.send_telegram_message(alert_chat_id, ticket_message)
        web_info_logger.info('Направлена информация в группу о созданном тикете %s', ticket_id)
        # Отправляем ответ о том, что всё принято и всё хорошо
        return "OK", 201

def handler_get_update_ticket():
        """Функция обработки GET запросов по URL"""
        ip_address = f"Request from {request.remote_addr}: {request.url}"
        user_agent = request.headers.get('User-Agent')
        user_who = f'User-Agent: {user_agent}'
        web_info_logger.info('Кто-то зашёл на сайт c IP-адреса: %s', ip_address)
        web_info_logger.info('Его данные подключения: %s', (user_who,))
        return Response('Этот URL для получение вэбхуков (обнова)', mimetype='text/plain')

def handler_post_update_ticket():
        """Функция обработки обновления тикета из HappyFox"""
        message = request.data.decode('utf-8')
        json_data, error = parse_json_message(message)
        if error:
            return Response(error, status=400)
        
        if json_data.get("update") is None:
            return Response(status=200)
        
        json_message_type = json_data["update"].get("message_type")
        if json_message_type == "Client Reply":
            result, error = handle_client_reply(json_data)
        elif json_data["update"].get("assignee_change") is not None:
            result, error = handle_assignee_change(json_data)
        elif json_data["update"].get("by").get("type") == "smartrule":
            if json_data["update"].get("by").get("name") == "Unresponded for 60 min":
                result, error = handle_unresponded_info_60(json_data)
            elif json_data["update"].get("by").get("name") == "Unresponded for 120 min":
                result, error = handle_unresponded_info_120(json_data)
            elif json_data["update"].get("by").get("name") == "Unresponded for 180 min":
                result, error = handle_unresponded_info_180(json_data)
            else:
                return Response(status=200)
        else:
            return Response(status=200)
        
        if error:
            return Response(error, status=400)
        return Response(result, status=201)

def handler_undersponed_ticket():
        """Функция обработки вебхука от HappyFox, если тикет был отложен"""
        message = ""
        message = request.data.decode('utf-8')
        try:
            # находим JSON в сообщении
            json_start = message.find('{')
            if json_start != -1:
                json_str = message[json_start:]
                # парсим JSON
                json_data = json.loads(json_str)
                print(json_data)
                web_info_logger.info('Направлена информация в группу о созданном тикете: %s', json_data)
            else:
                web_error_logger.error("JSON не найден в сообщении. %s")
                return 'JSON не найден в сообщении.', 400
        except ValueError as error_message:
            web_error_logger.error("Не удалось распарсить JSON в запросе. %s", error_message)
            return 'Не удалось распарсить JSON в запросе.', 500
        
        # Отправляем ответ о том, что всё принято и всё хорошо
        return "OK", 201

def handler_get_yandex_oauth_callback():
        """Функция определения oauth яндекса"""
        # Извлеките авторизационный код из URL
        authorization_code = request.args.get('code')
        if not authorization_code:
            return Response('Ошибка: авторизационный код не найден', mimetype='text/plain')

        # Запросите OAuth-токен, используя авторизационный код
        token_request_data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": "8525a645d7744d008ea42465c080b2a7",
            "client_secret": "1b9335d34574471b894d1c2576305a11",
            "redirect_uri": "http://194.37.1.214:3030/yandex_oauth_callback"
        }
        token_response = requests.post('https://oauth.yandex.ru/token', data=token_request_data, timeout=30)

        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data['access_token']

            # Отправляем в ответ браузера access_token, который нужно сохранить
            return Response(f'OAuth-токен успешно получен: {access_token}', mimetype='text/plain')
        # Если ошибка, отправим её
        return Response('Ошибка: не удалось получить OAuth-токен', mimetype='text/plain', status=400)

def api_data_release_versions():
        """Функция получения номеров версий отправки рассылки через API"""
        try:
            # Определяем список для хранения версий рассылок
            versions = []
            # Используем контекстный менеджер для выполнения операций с БД и автоматического закрытия соединения
            with conn:
                # Делаем выборку из таблицы Release_info по уникальным значениям даты и номера релиза
                for row in Release_info.select(Release_info.date, Release_info.release_number).distinct():
                    # Добавляем в список версий новую версию рассылки
                    versions.append({'Data': row.date, 'Number': row.release_number})
        except peewee.OperationalError as error_message:
            # Обработка исключения при возникновении ошибки подключения к БД
            web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
            print("Ошибка подключения к базе данных SQLite:", error_message)
            return "Ошибка с БД"
        # Формируем JSON с отступами для улучшения читабельности
        json_data = json.dumps(versions, ensure_ascii=False, indent=4)
        # Устанавливаем заголовок Access-Control-Allow-Origin
        response = Response(json_data, content_type='application/json; charset=utf-8')
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON
        return response

def api_data_release_number(version):
        """Функция просмотра контактов, кому ушла рассылка через API"""
        # Подключение к базе данных SQLite
        try:
            with conn:
                # Фильтрация данных по номеру релиза
                query = Release_info.select().where(Release_info.release_number == version)
                rows = list(query)
        except peewee.OperationalError as error_message:
            web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
            print("Ошибка подключения к базе данных SQLite:", error_message)
            return error_message
        # Создаём пустой массив
        data = []
        # Преобразование полученных данных в список словарей
        for row in rows:
            copy_addresses = []
            # Разбиваем строку со списком адресов электронной почты для копии на отдельные адреса
            if row.copy is None:
                copy_dict = [{'1': 'Копии отсутствуют'}]
            else:
                copy_addresses = row.copy.split(', ')
                # Формируем словарь для копий, который содержит адреса электронной почты с ключами 1, 2, 3 и т.д.
                copy_dict = [{f"{i+1}": copy_addresses[i]} for i in range(len(copy_addresses))]
            contacts = {
                'Main': row.main_contact,
                'Copy': copy_dict
            }
            # Добавляем данные в созданный ранее массив (создаём структуру данных JSON)
            data.append({
                'Data': row.date,
                'Number': row.release_number,
                'Client': row.client_name,
                'Contacts': contacts
            })
        # Форматирование JSON с отступами для улучшения читабельности
        json_data = json.dumps(data, ensure_ascii=False, indent=4)
        # Создание ответа с типом содержимого application/json и кодировкой UTF-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавление заголовка Access-Control-Allow-Origin для разрешения кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправка ответа JSON
        return response

def data_release_html():
        release_number = request.args.get('release_number', 'all')
        onn = sqlite3.connect(f'file:{db_filename}')
        cur = onn.cursor()
        if release_number == 'all':
            cur.execute('SELECT * FROM info')
        else:
            cur.execute('SELECT * FROM info WHERE "Номер_релиза" = ?', (release_number,))
        rows = cur.fetchall()
        onn.close()
        data = []
        for row in rows:
            data.append({
                'Дата_рассылки': row[0],
                'Номер_релиза': row[1],
                'Наименование_клиента': row[2],
                'Основной_контакт': row[3],
                'Копия': row[4]
            })
        return render_template('data_release.html', data=data)

def get_BM_Info_onClient_api():
    try:
        # Используем контекстный менеджер для выполнения операций с БД
        with conn:
            # Получаем все записи из таблицы client_info
            client_infos = list(BMInfo_onClient.select())
        # Создаем список для хранения результатов
        results = []
        for client_info in client_infos:
            # Создаем словарь для хранения данных одного клиента
            result = {}
            for column_name in client_info.column_names:
                # Используем названия столбцов для извлечения данных из объекта BMInfo_onClient
                result[column_name] = getattr(client_info, column_name)
                #  Используйте русские названия столбцов
                # result[RU_COLUMN_NAMES[column_name]] = getattr(client_info, column_name.lower())
            # Добавляем словарь с данными клиента в список результатов
            results.append(result)
        # Преобразуем список результатов в строку JSON
        json_data = json.dumps(results, ensure_ascii=False, indent=4)
        # Создаем ответ с заголовком Content-Type и кодировкой utf-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавляем заголовок Access-Control-Allow-Origin для поддержки кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON
        return response
    
    except Exception as error:
        # Если возникла ошибка, формируем словарь с информацией об ошибке
        error_message = {"error": str(error)}
        # Преобразуем словарь с информацией об ошибке в строку JSON
        json_data = json.dumps(error_message, ensure_ascii=False, indent=4)
        # Создаем ответ с заголовком Content-Type и кодировкой utf-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавляем заголовок Access-Control-Allow-Origin для поддержки кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON с информацией об ошибке
        return response

def post_BM_Info_onClient_api():
    """
    Функция добавления информации о клиентах в БД через API.
    Обрабатывает HTTP POST-запросы и сохраняет информацию о клиентах
    в базе данных.
    """
    try:
        # Получаем данные из запроса и создаем объект BMInfo_onClient
        data = json.loads(request.data.decode('utf-8'))
        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([BMInfo_onClient, ClientsCard])

        # Создаем транзакцию для сохранения данных в БД
        with conn.atomic():
            # Проверяем наличие существующего клиента с тем же именем
            existing_client = BMInfo_onClient.get_or_none(BMInfo_onClient.client_name == data['client_name'])
            if existing_client is None:
                # Создаем запись в таблице BMInfo_onClient
                new_client = BMInfo_onClient.create(
                    client_name=data['client_name'],
                    contact_status=data['contact_status'],
                    notes=data.get('notes')
                )
                # Получаем id созданной записи
                client_id = new_client.id

                # Создаем запись в таблице ClientsCard с полученным client_id
                new_client_card = ClientsCard.create(client_id=client_id)

                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                print(f"Клиент с именем {data['client_name']} уже существует. Пропускаем...")
                return f"Клиент с именем {data['client_name']} уже существует. Пропускаем...", 409

        web_info_logger.info("Добавлен клиент в БД: %s", data['client_name'])
        return 'Клиент успешно записаны в БД!', 201

    except peewee.OperationalError as error_message:
        # Обработка исключения при возникновении ошибки подключения к БД
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        web_error_logger.error("Ошибка подключения к базе данных SQLite:%s", error_message)
        return f"Ошибка с БД: {error_message}", 500
    except Exception as error:
        # Обработка остальных исключений
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}", 500

def patch_BM_Info_onClient_api():
    """Функция обновления данных в БД (обязательный ключ - client_name)"""
    data = request.get_json()

    # Получаем имя клиента, которое нужно обновить
    client_name = data.get('client_name', None)

    if not client_name:
        return 'Необходимо указать имя клиента для обновления', 400

    # Получаем обновленные данные
    updated_data = {key: value for key, value in data.items() if key != 'client_name'}

    if not updated_data:
        return 'Необходимо предоставить данные для обновления', 400

    try:
        with conn:
            # Обновляем запись с указанным именем клиента
            updated_rows = (BMInfo_onClient.update(updated_data).where(BMInfo_onClient.client_name == client_name).execute())

        if updated_rows > 0:
            return f'Обновлено {updated_rows} записей с именем клиента: {client_name}', 200
        else:
            return f'Клиент с именем {client_name} не найден', 404

    except peewee.OperationalError as error_message:
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        return jsonify({"message": f"Ошибка сервера: {error}", "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}), 500

def delete_BM_Info_onClient_api():
    """Функция удаления клиента из БД (ключ для приёма - client_name)"""
    # Получение данных из запроса в формате JSON
    data = request.get_json()
    # Извлечение имени клиента из данных запроса, значение по умолчанию - None
    client_name = data.get('client_name', None)

    # Проверка наличия имени клиента в запросе
    if not client_name:
        return 'Необходимо указать имя клиента для удаления', 400

    try:
        # Открываем соединение с базой данных
        with conn:
            # Удаление записи с указанным именем клиента
            deleted_rows = BMInfo_onClient.delete().where(BMInfo_onClient.client_name == client_name).execute()
        # Если удалена хотя бы одна запись, возвращаем количество удаленных записей и успешный статус
        if deleted_rows > 0:
            return f'Удалено {deleted_rows} записей с именем клиента: {client_name}', 200
        else:
            # Если запись с указанным именем клиента не найдена, возвращаем ошибку 404
            return f'Клиент с именем {client_name} не найден', 404

    except peewee.OperationalError as error_message:
        # Обработка ошибки подключения к базе данных SQLite
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        # Обработка остальных ошибок сервера
        return f"Ошибка сервера: {error}", 500

def get_client_card_api():
    """Функция получения данных в БД со списком карточек клиентов"""
    try:
        # Используем контекстный менеджер для выполнения операций с БД
        with conn:
            # Получаем все записи из таблицы ClientsCard
            client_cards = list(ClientsCard.select())
        
        # Создаем список для хранения результатов
        results = []
        for client_card in client_cards:
            # Создаем словарь для хранения данных одной карточки клиента
            result = {}
            for column_name in client_card.column_names:
                # Используем названия столбцов для извлечения данных из объекта ClientsCard
                result[column_name] = getattr(client_card, column_name)
            # Добавляем словарь с данными карточки клиента в список результатов
            results.append(result)
        
        # Преобразуем список результатов в строку JSON
        json_data = json.dumps(results, ensure_ascii=False, indent=4)
        # Создаем ответ с заголовком Content-Type и кодировкой utf-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавляем заголовок Access-Control-Allow-Origin для поддержки кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON
        return response

    except Exception as error:
        # Если возникла ошибка, формируем словарь с информацией об ошибке
        error_message = {"error": str(error)}
        # Преобразуем словарь с информацией об ошибке в строку JSON
        json_data = json.dumps(error_message, ensure_ascii=False, indent=4)
        # Создаем ответ с заголовком Content-Type и кодировкой utf-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавляем заголовок Access-Control-Allow-Origin для поддержки кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON с информацией об ошибке
        return response

def get_client_by_id(id):
    """Функция возвращает данные клиента по указанному id (client_id)."""
    try:
        with conn:
            # Получаем данные клиента по id
            client = ClientsCard.get_or_none(ClientsCard.client_id == id)

            if client is None:
                # Если клиент с указанным ID не найден, возвращаем сообщение об ошибке
                message = "Клиент с ID {} не найден".format(id)
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            bm_client = BMInfo_onClient.get_or_none(BMInfo_onClient.client_info == id)

            if bm_client is None:
                message = "Информация о клиенте с ID {} не найдена в таблице BM_info_on_clients".format(id)
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            # Преобразованием данных и формируем ответ
            client_data = {
                'client_id': client.client_id,
                'client_name': bm_client.client_name,
                'contact_status': bm_client.contact_status
            }

            json_data = json.dumps(client_data, ensure_ascii=False, indent=4)
            response = Response(json_data, content_type='application/json; charset=utf-8')
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

    except peewee.OperationalError as error_message:
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        print("Ошибка подключения к базе данных SQLite:", error_message)
        message = "Ошибка подключения к базе данных SQLite: {}".format(error_message)
        json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as error:
        web_error_logger.error("Ошибка сервера: %s", error)
        print("Ошибка сервера:", error)
        message = "Ошибка сервера: {}".format(error)
        json_data = json.dumps({"message": message, "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

def post_client_card_api():
    """Функция добавления данных карточек клиентов в БД"""
    try:
        # Получаем данные из запроса и создаем объект ClientsCard
        data = json.loads(request.data.decode('utf-8'))
        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([ClientsCard])

        # Создаем транзакцию для сохранения данных в БД
        with conn.atomic():
            # Проверяем наличие существующего клиента с тем же ID
            existing_client = ClientsCard.get_or_none(ClientsCard.client_id == data['client_id'])
            if existing_client is None:
                # Сохраняем данные в базе данных, используя insert и execute
                ClientsCard.insert(**data).execute()
                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                print(f"Контакт с ID {data['client_id']} уже существует. Пропускаем...")
                return f"Контакт с ID {data['client_id']} уже существует. Пропускаем...", 409

        web_info_logger.info("Добавлен контакт в БД: %s", data['client_id'])
        return 'Контакт успешно записаны в БД!', 201

    except peewee.OperationalError as error_message:
        # Обработка исключения при возникновении ошибки подключения к БД
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        web_error_logger.error("Ошибка подключения к базе данных SQLite:%s", error_message)
        return f"Ошибка с БД: {error_message}"
    except Exception as error:
        # Обработка остальных исключений
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}"

def post_client_card_api_by_id(id):
    """Функция добавления данных карточек клиентов в БД с указанным id клиента"""
    try:
        # Получаем данные из запроса и создаем объект ClientsCard
        data = json.loads(request.data.decode('utf-8'))
        # Добавляем переданный id клиента в данные
        data['client_id'] = id
        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([ClientsCard])

        # Создаем транзакцию для сохранения данных в БД
        with conn.atomic():
            # Проверяем наличие существующего клиента с тем же ID
            existing_client = ClientsCard.get_or_none(ClientsCard.client_id == id)
            if existing_client is None:
                # Сохраняем данные в базе данных, используя insert и execute
                ClientsCard.insert(**data).execute()
                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                print(f"Карточка клиента с ID {id} уже существует. Пропускаем...")
                return f"Карточка клиента с ID {id} уже существует. Пропускаем..."

        web_info_logger.info("Добавлена карточка клиента с ID: %s", id)
        return 'Data successfully saved to the database!'

    except peewee.OperationalError as error_message:
        # Обработка исключения при возникновении ошибки подключения к БД
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        web_error_logger.error("Ошибка подключения к базе данных SQLite:%s", error_message)
        return f"Ошибка с БД: {error_message}"
    except Exception as error:
        # Обработка остальных исключений
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}"

def patch_client_card_api(id):
    """Функция изменений данных в БД со списком карточек клиентов"""
    data = request.get_json()

    # Получаем обновленные данные
    updated_data = {key: value for key, value in data.items() if key != 'client_id'}

    if not updated_data:
        return 'Необходимо предоставить данные для обновления', 400

    try:
        with conn:
            # Обновляем запись с указанным ID клиента
            updated_rows = (BMInfo_onClient.update(updated_data).where(BMInfo_onClient.client_info == id).execute())

        if updated_rows > 0:
            return f'Обновлено {updated_rows} записей с ID клиента: {id}', 200
        else:
            return f'Клиент с ID {id} не найден', 404

    except peewee.OperationalError as error_message:
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        return jsonify({"message": f"Ошибка сервера: {error}", "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}), 500

def delete_client_card_api():
    """Функция удаления данных в БД со списком карточек клиентов"""
    # Получение данных из запроса в формате JSON
    data = request.get_json()
    # Извлечение ID клиента из данных запроса, значение по умолчанию - None
    clients_id = data.get('clients_id', None)

    # Проверка наличия ID клиента в запросе
    if not clients_id:
        return 'Необходимо указать ID клиента для удаления', 400

    try:
        # Открываем соединение с базой данных
        with conn:
            # Удаление записи с указанным ID клиента
            deleted_rows = ClientsCard.delete().where(ClientsCard.clients_id == clients_id).execute()
        # Если удалена хотя бы одна запись, возвращаем количество удаленных записей и успешный статус
        if deleted_rows > 0:
            return f'Удалено {deleted_rows} записей с ID клиента: {clients_id}', 200
        else:
            # Если запись с указанным ID клиента не найдена, возвращаем ошибку 404
            return f'Клиент с ID {clients_id} не найден', 404

    except peewee.OperationalError as error_message:
        # Обработка ошибки подключения к базе данных SQLite
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        # Обработка остальных ошибок сервера
        return f"Ошибка сервера: {error}", 500

def get_contact_by_client_id(id):
    """Функция возвращает информацию о контактах для клиента с указанным client_id."""
    try:
        with conn:
            # Получаем контакты клиента по client_id
            client = ClientsCard.get_or_none(ClientsCard.client_id == id)

            if client is None:
                message = "Клиент с ID {} не найден".format(id)
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            
            contact_id = client.contacts
            contacts = ContactsCard.select().where(ContactsCard.contact_id == contact_id)

            if not contacts.exists():
                message = "Контакты для клиента с ID {} не найдены".format(contact_id)
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            client_name = BMInfo_onClient.get(BMInfo_onClient.client_info == id).client_name

            contacts_data = []
            for contact in contacts:
                contacts_data.append({
                    'contact_name': contact.contact_name,
                    'contact_email': contact.contact_email,
                    'contact_position': contact.contact_position,
                    'notification_update': contact.notification_update,
                    'contact_notes': contact.contact_notes
                })

            result = {
                'client': client_name,
                'client_id': id,
                'contacts': contacts_data
            }

            json_data = json.dumps(result, ensure_ascii=False, indent=4)
            response = Response(json_data, content_type='application/json; charset=utf-8')
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

    except peewee.OperationalError as error_message:
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        print("Ошибка подключения к базе данных SQLite:", error_message)
        message = "Ошибка подключения к базе данных SQLite: {}".format(error_message)
        json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as error:
        web_error_logger.error("Ошибка сервера: %s", error)
        print("Ошибка сервера:", error)
        message = "Ошибка сервера: {}".format(error)
        json_data = json.dumps({"message": message, "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

def post_contact_api_by_id(id):
    """Функция добавления контактов в БД с указанным id клиента."""
    try:
        # Получаем данные из запроса
        data = json.loads(request.data.decode('utf-8'))
        
        # Проверяем обязательные поля
        if 'contact_name' not in data or 'contact_email' not in data:
            return 'Ошибка: "contact_name" и "contact_email" являются обязательными полями.', 400

        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([ContactsCard, ClientsCard])

        # Получаем значение contacts для указанного client_id из таблицы ClientsCard
        client = ClientsCard.get_or_none(ClientsCard.client_id == id)
        if client is None:
            return f"Ошибка: клиент с ID {id} не найден.", 404

        # Добавляем значение contacts в данные
        data['contact_id'] = client.contacts

        # Создаем транзакцию для сохранения данных в БД
        with conn.atomic():
            # Проверяем наличие существующего контакта с тем же email
            existing_contact = ContactsCard.get_or_none(ContactsCard.contact_email == data['contact_email'])

            if existing_contact is None:
                # Сохраняем данные в базе данных, используя insert и execute
                ContactsCard.insert(**data).execute()
                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                return f"Контакт с email {data['contact_email']} уже существует. Пропускаем...", 409

        web_info_logger.info("Добавлен контакт для клиента с ID: %s", id)
        return 'Contact data successfully saved to the database!', 201
    
    except peewee.IntegrityError as error:
        # Обработка исключения при нарушении ограничений целостности
        web_error_logger.error("Ошибка целостности данных: %s", error)
        return f"Ошибка: указанный Email {data['contact_email']} уже есть в БД.", 409
    
    except peewee.OperationalError as error_message:
        # Обработка исключения при возникновении ошибки подключения к БД
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        web_error_logger.error("Ошибка подключения к базе данных SQLite:%s", error_message)
        return f"Ошибка с БД: {error_message}", 500
    
    except Exception as error:
        # Обработка остальных исключений
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}", 500

def get_connect_info_api():
    """Функция получения данных в БД со списком контактов клиентов"""
    try:
        # Используем контекстный менеджер для выполнения операций с БД
        with conn:
            # Получаем все записи из таблицы ConnectInfoCard
            connect_infos = list(СonnectInfoCard.select())
        
        # Создаем список для хранения результатов
        results = []
        for connect_info in connect_infos:
            # Создаем словарь для хранения данных одной записи контакта клиента
            result = {}
            for column_name in connect_info.column_names:
                # Используем названия столбцов для извлечения данных из объекта СonnectInfoCard
                result[column_name] = getattr(connect_info, column_name)
            # Добавляем словарь с данными контакта клиента в список результатов
            results.append(result)
        
        # Преобразуем список результатов в строку JSON
        json_data = json.dumps(results, ensure_ascii=False, indent=4)
        # Создаем ответ с заголовком Content-Type и кодировкой utf-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавляем заголовок Access-Control-Allow-Origin для поддержки кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON
        return response

    except Exception as error:
        # Если возникла ошибка, формируем словарь с информацией об ошибке
        error_message = {"error": str(error)}
        # Преобразуем словарь с информацией об ошибке в строку JSON
        json_data = json.dumps(error_message, ensure_ascii=False, indent=4)
        # Создаем ответ с заголовком Content-Type и кодировкой utf-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавляем заголовок Access-Control-Allow-Origin для поддержки кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON с информацией об ошибке
        return response

def get_connect_info_by_id(id):
    """Функция возвращает информацию о подключении по указанному client_id."""
    try:
        with conn:
            # Получаем информацию о подключении по client_id
            connect_infos = СonnectInfoCard.select().where(СonnectInfoCard.client_id == id)

            if not connect_infos.exists():
                # Если информация о подключении с указанным ID не найдена, возвращаем сообщение об ошибке
                message = "Информация о подключении с ID {} не найдена".format(id)
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            # Здесь продолжайте с преобразованием данных и формированием ответа
            connect_infos_data = [
                {
                    'id': info.id,
                    'client_id': info.client_id,
                    'contact_info_name': info.contact_info_name,
                    'contact_info_account': info.contact_info_account,
                    'contact_info_password': info.contact_info_password
                } for info in connect_infos
            ]

            json_data = json.dumps(connect_infos_data, ensure_ascii=False, indent=4)
            response = Response(json_data, content_type='application/json; charset=utf-8')
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

    except peewee.OperationalError as error_message:
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        print("Ошибка подключения к базе данных SQLite:", error_message)
        message = "Ошибка подключения к базе данных SQLite: {}".format(error_message)
        json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as error:
        web_error_logger.error("Ошибка сервера: %s", error)
        print("Ошибка сервера:", error)
        message = "Ошибка сервера: {}".format(error)
        json_data = json.dumps({"message": message, "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

def post_connect_info_api():
    """Функция добавления информации о подключении в БД."""
    try:
        # Получаем данные из запроса
        data = json.loads(request.data.decode('utf-8'))

        # Проверяем обязательные поля
        if 'contact_info_name' not in data or 'contact_info_account' not in data or 'contact_info_password' not in data:
            return 'Ошибка: "contact_info_name", "contact_info_account" и "contact_info_password" являются обязательными полями.', 400

        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([СonnectInfoCard])

        # Создаем транзакцию для сохранения данных в БД
        with conn.atomic():
            # Проверяем наличие существующей записи с тем же contact_info_name, contact_info_account и client_id
            existing_info = СonnectInfoCard.get_or_none(
                (СonnectInfoCard.contact_info_name == data['contact_info_name']) &
                (СonnectInfoCard.contact_info_account == data['contact_info_account']) &
                (СonnectInfoCard.client_id == data['client_id'])
            )

            if existing_info is None:
                # Сохраняем данные в базе данных, используя insert и execute
                СonnectInfoCard.insert(**data).execute()
                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                # Обновляем существующую запись с данными из запроса
                СonnectInfoCard.update(**data).where(
                    (СonnectInfoCard.contact_info_name == data['contact_info_name']) &
                    (СonnectInfoCard.contact_info_account == data['contact_info_account']) &
                    (СonnectInfoCard.client_id == data['client_id'])
                ).execute()
                # Сохраняем изменения в БД
                conn.commit()

        web_info_logger.info("Добавлена/обновлена информация о подключении с ID: %s", data['client_id'])
        return 'Connect info data successfully saved to the database!', 201

    except peewee.OperationalError as error_message:
        # Обработка исключения при возникновении ошибки подключения к БД
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        return f"Ошибка с БД: {error_message}", 500
    except Exception as error:
        # Обработка остальных исключений
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}", 500

def delete_connect_info_api(id):
    """Функция удаления записи с информацией о подключении к клиенту по ID"""
    try:
        with conn:
            # Удаляем запись с указанным ID
            deleted_rows = СonnectInfoCard.delete().where(СonnectInfoCard.id == id).execute()

        if deleted_rows > 0:
            return f'Удалено {deleted_rows} записей с ID: {id}', 200
        else:
            return f'Запись с ID {id} не найдена', 404

    except peewee.OperationalError as error_message:
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        return jsonify({"message": f"Ошибка сервера: {error}", "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}), 500

def patch_connect_info_api(id):
    """Функция обновления информации о подключении к клиенту по ID"""
    data = request.get_json()

    # Получаем обновленные данные
    updated_data = {key: value for key, value in data.items() if key in СonnectInfoCard.COLUMN_NAMES and key != 'id'}

    if not updated_data:
        return 'Необходимо предоставить данные для обновления', 400

    try:
        with conn:
            # Обновляем запись с указанным ID
            updated_rows = СonnectInfoCard.update(updated_data).where(СonnectInfoCard.id == id).execute()

        if updated_rows > 0:
            return f'Обновлено {updated_rows} записей с ID: {id}', 200
        else:
            return f'Запись с ID {id} не найдена', 404

    except peewee.OperationalError as error_message:
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        return jsonify({"message": f"Ошибка сервера: {error}", "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}), 500

def get_bm_servers_card_api(client_id):
    try:
        with conn:
            # Получаем запись клиента с указанным ID
            client = ClientsCard.get_or_none(ClientsCard.client_id == client_id)
            if client is None:
                return f'Клиент с ID {client_id} не найден', 404

            # Получаем записи из таблицы BMServersCard, связанные с указанным клиентом
            bm_servers_cards = BMServersCard.select().where(BMServersCard.bm_servers_id == client_id)

            # Конвертируем результат в JSON
            result = []
            for bm_server in bm_servers_cards:
                server_data = {}
                for column_name in BMServersCard.COLUMN_NAMES:
                    server_data[column_name] = getattr(bm_server, column_name)
                result.append(server_data)

            return jsonify(result), 200

    except peewee.OperationalError as error_message:
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        return jsonify({"message": f"Ошибка сервера: {error}", "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}), 500

def post_bm_servers_card_api(client_id):
    try:
        data = request.get_json()
        if not data:
            return 'Необходимо предоставить данные для создания записи', 400

        required_fields = ['bm_servers_circuit', 'bm_servers_servers_name', 'bm_servers_servers_adress', 'bm_servers_role']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return f"Отсутствуют обязательные поля: {', '.join(missing_fields)}", 400

        # Проверяем, существует ли клиент с указанным ID
        with conn:
            client = ClientsCard.get_or_none(ClientsCard.client_id == client_id)
            if client is None:
                return f'Клиент с ID {client_id} не найден', 404

            # Создаем новую запись и связываем ее с клиентом
            new_bm_server = BMServersCard.create(
                bm_servers_id=client_id,
                bm_servers_circuit=data['bm_servers_circuit'],
                bm_servers_servers_name=data['bm_servers_servers_name'],
                bm_servers_servers_adress=data['bm_servers_servers_adress'],
                bm_servers_operation_system=data.get('bm_servers_operation_system', None),
                bm_servers_url=data.get('bm_servers_url', None),
                bm_servers_role=data['bm_servers_role']
            )
            new_bm_server.save()

        return f"Запись успешно создана с ID: {new_bm_server.bm_servers_id}", 201

    except peewee.OperationalError as error_message:
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        return jsonify({"message": f"Ошибка сервера: {error}", "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}), 500

def get_integration_api(client_id):
    try:
        with conn:
            client = BMInfo_onClient.get(BMInfo_onClient.client_info == client_id)
    except DoesNotExist:
        return jsonify({'error': 'Client not found'}), 404

    integration_id = client.integration

    try:
        with conn:
            integration = Integration.get(Integration.integration_id == integration_id)
    except DoesNotExist:
        return jsonify({'error': 'Integration not found'}), 404

    result = {}
    for column in Integration.COLUMN_NAMES:
        if column != 'integration_id':
            result[column] = getattr(integration, column)

    return jsonify(result)

def post_integration_api(client_id):
    try:
        with conn:
            client = BMInfo_onClient.get(BMInfo_onClient.client_info == client_id)
    except DoesNotExist:
        return jsonify({'error': 'Client not found'}), 404

    integration_id = client.integration
    data = request.json

    # Создаем словарь с значениями по умолчанию
    default_data = {key: False for key in Integration.COLUMN_NAMES}
    default_data['integration_id'] = integration_id

    # Обновляем значения по умолчанию данными из POST-запроса
    default_data.update(data)

    try:
        with conn:
            integration = Integration.create(**default_data)
    except peewee.IntegrityError:
        return jsonify({'error': 'Integration already exists'}), 409

    return jsonify({'message': 'Integration created successfully'}), 201

def get_app():
    """Функция приложения ВЭБ-сервера"""
    app = Flask(__name__)

    @app.route('/', methods=['GET'])
    def handle_get():
        """Функция обработки вэбхуков из HappyFox"""
        ip_address = f"Request from {request.remote_addr}: {request.url}"
        user_agent = request.headers.get('User-Agent')
        user_who = f'User-Agent: {user_agent}'
        web_info_logger.info('Кто-то зашёл на сайт c IP-адреса: %s', ip_address)
        web_info_logger.info('Его данные подключения: %s', (user_who,))
        return Response('Site', mimetype='text/plain')
    
    @app.route('/create_ticket', methods=['GET'])
    def handle_get_create_ticket():
        """Функция обработки вэбхуков из HappyFox"""
        ip_address = f"Request from {request.remote_addr}: {request.url}"
        user_agent = request.headers.get('User-Agent')
        user_who = f'User-Agent: {user_agent}'
        web_info_logger.info('Кто-то зашёл на сайт c IP-адреса: %s', ip_address)
        web_info_logger.info('Его данные подключения: %s', (user_who,))
        return Response('Этот URL для получения вэбхуков(создание)', mimetype='text/plain')
    
    @app.route('/create_ticket', methods=['POST'])
    def create_ticket():
        """Функция обработки создания тикета из HappyFox"""
        message = request.data.decode('utf-8')
        # парсим JSON-строку
        json_data, error = parse_json_message(message)
        if error:
            return error, 400
        # находим значения для ключей
        ticket_id = json_data.get("ticket_id")
        subject = json_data.get("subject")
        priority_name = json_data.get("priority_name")
        agent_ticket_url = json_data.get("agent_ticket_url")
        # отправляем сообщение в телеграм-бот
        ticket_message = (f"Новый тикет: {ticket_id}\nТема: {subject}\nПриоритет: {priority_name}\nСсылка: {agent_ticket_url}")
        # открываем файл и загружаем данные
        with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
            data = json.load(file)
        # извлекаем значения GROUP_ALERT_NEW_TICKET из SEND_ALERT
        alert_chat_id = data['SEND_ALERT']['GROUP_ALERT_NEW_TICKET']
        alert.send_telegram_message(alert_chat_id, ticket_message)
        web_info_logger.info('Направлена информация в группу о созданном тикете %s', ticket_id)
        # Отправляем ответ о том, что всё принято и всё хорошо
        return "OK", 201

    @app.route('/update_ticket', methods=['GET'])
    def handle_get_update_ticket():
        """Функция обработки вэбхуков из HappyFox"""
        ip_address = f"Request from {request.remote_addr}: {request.url}"
        user_agent = request.headers.get('User-Agent')
        user_who = f'User-Agent: {user_agent}'
        web_info_logger.info('Кто-то зашёл на сайт c IP-адреса: %s', ip_address)
        web_info_logger.info('Его данные подключения: %s', (user_who,))
        return Response('Этот URL для получение вэбхуков (обнова)', mimetype='text/plain')
    
    @app.route('/update_ticket', methods=['POST'])
    def update_ticket():
        """Функция обработки обновления тикета из HappyFox"""
        message = request.data.decode('utf-8')
        json_data, error = parse_json_message(message)
        if error:
            return Response(error, status=400)
        
        if json_data.get("update") is None:
            return Response(status=200)
        
        json_message_type = json_data["update"].get("message_type")
        if json_message_type == "Client Reply":
            result, error = handle_client_reply(json_data)
        elif json_data["update"].get("assignee_change") is not None:
            result, error = handle_assignee_change(json_data)
        elif json_data["update"].get("by").get("type") == "smartrule":
            if json_data["update"].get("by").get("name") == "Unresponded for 60 min":
                result, error = handle_unresponded_info_60(json_data)
            elif json_data["update"].get("by").get("name") == "Unresponded for 120 min":
                result, error = handle_unresponded_info_120(json_data)
            elif json_data["update"].get("by").get("name") == "Unresponded for 180 min":
                result, error = handle_unresponded_info_180(json_data)
            else:
                return Response(status=200)
        else:
            return Response(status=200)
        
        if error:
            return Response(error, status=400)
        return Response(result, status=201)

    @app.route('/undersponed_ticket', methods=['POST'])
    def undersponed_ticket():
        """Функция обработки вебхука от HappyFox, если тикет был отложен"""
        message = ""
        message = request.data.decode('utf-8')
        try:
            # находим JSON в сообщении
            json_start = message.find('{')
            if json_start != -1:
                json_str = message[json_start:]
                # парсим JSON
                json_data = json.loads(json_str)
                print(json_data)
                web_info_logger.info('Направлена информация в группу о созданном тикете: %s', json_data)
            else:
                web_error_logger.error("JSON не найден в сообщении. %s")
                return 'JSON не найден в сообщении.', 400
        except ValueError as error_message:
            web_error_logger.error("Не удалось распарсить JSON в запросе. %s", error_message)
            return 'Не удалось распарсить JSON в запросе.', 500
        
        # Отправляем ответ о том, что всё принято и всё хорошо
        return "OK", 201
    
    @app.route('/yandex_oauth_callback', methods=['GET'])
    def handle_get_yandex_oauth_callback():
        """Функция определения oauth яндекса"""
        # Извлеките авторизационный код из URL
        authorization_code = request.args.get('code')
        if not authorization_code:
            return Response('Ошибка: авторизационный код не найден', mimetype='text/plain')

        # Запросите OAuth-токен, используя авторизационный код
        token_request_data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": "8525a645d7744d008ea42465c080b2a7",
            "client_secret": "1b9335d34574471b894d1c2576305a11",
            "redirect_uri": "http://194.37.1.214:3030/yandex_oauth_callback"
        }
        token_response = requests.post('https://oauth.yandex.ru/token', data=token_request_data, timeout=30)

        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data['access_token']

            # Отправляем в ответ браузера access_token, который нужно сохранить
            return Response(f'OAuth-токен успешно получен: {access_token}', mimetype='text/plain')
        # Если ошибка, отправим её
        return Response('Ошибка: не удалось получить OAuth-токен', mimetype='text/plain', status=400)

    @app.route('/yandex_oauth_callback', methods=['POST'])
    def handle_post_yandex_oauth_callback():
        
        return "OK", 201

    @app.route('/data_release/api/versions', methods=['GET'])
    def api_data_release_versions():
        """Функция получения номеров версий отправки рассылки через API"""
        try:
            # Определяем список для хранения версий рассылок
            versions = []
            # Используем контекстный менеджер для выполнения операций с БД и автоматического закрытия соединения
            with conn:
                # Делаем выборку из таблицы Release_info по уникальным значениям даты и номера релиза
                for row in Release_info.select(Release_info.date, Release_info.release_number).distinct():
                    # Добавляем в список версий новую версию рассылки
                    versions.append({'Data': row.date, 'Number': row.release_number})
        except peewee.OperationalError as error_message:
            # Обработка исключения при возникновении ошибки подключения к БД
            web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
            print("Ошибка подключения к базе данных SQLite:", error_message)
            return "Ошибка с БД"
        # Формируем JSON с отступами для улучшения читабельности
        json_data = json.dumps(versions, ensure_ascii=False, indent=4)
        # Устанавливаем заголовок Access-Control-Allow-Origin
        response = Response(json_data, content_type='application/json; charset=utf-8')
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON
        return response

    # Определение маршрута для API с аргументом 'version' в URL
    @app.route('/data_release/api/<string:version>', methods=['GET'])
    # Применение декоратора require_basic_auth для аутентификации пользователей
    @require_basic_auth(USERNAME, PASSWORD)
    def api_data_release_number(version):
        """Функция просмотра контактов, кому ушла рассылка через API"""
        # Подключение к базе данных SQLite
        try:
            with conn:
                # Фильтрация данных по номеру релиза
                query = Release_info.select().where(Release_info.release_number == version)
                rows = list(query)
        except peewee.OperationalError as error_message:
            web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
            print("Ошибка подключения к базе данных SQLite:", error_message)
            return error_message
        # Создаём пустой массив
        data = []
        # Преобразование полученных данных в список словарей
        for row in rows:
            copy_addresses = []
            # Разбиваем строку со списком адресов электронной почты для копии на отдельные адреса
            if row.copy is None:
                copy_dict = [{'1': 'Копии отсутствуют'}]
            else:
                copy_addresses = row.copy.split(', ')
                # Формируем словарь для копий, который содержит адреса электронной почты с ключами 1, 2, 3 и т.д.
                copy_dict = [{f"{i+1}": copy_addresses[i]} for i in range(len(copy_addresses))]
            contacts = {
                'Main': row.main_contact,
                'Copy': copy_dict
            }
            # Добавляем данные в созданный ранее массив (создаём структуру данных JSON)
            data.append({
                'Data': row.date,
                'Number': row.release_number,
                'Client': row.client_name,
                'Contacts': contacts
            })
        # Форматирование JSON с отступами для улучшения читабельности
        json_data = json.dumps(data, ensure_ascii=False, indent=4)
        # Создание ответа с типом содержимого application/json и кодировкой UTF-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавление заголовка Access-Control-Allow-Origin для разрешения кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправка ответа JSON
        return response

    # Обработчик сайта с данными о релизе
    @app.route('/data_release', methods=['GET'])
    def data_release_html():
        release_number = request.args.get('release_number', 'all')
        onn = sqlite3.connect(f'file:{db_filename}')
        cur = onn.cursor()
        if release_number == 'all':
            cur.execute('SELECT * FROM info')
        else:
            cur.execute('SELECT * FROM info WHERE "Номер_релиза" = ?', (release_number,))
        rows = cur.fetchall()
        onn.close()
        data = []
        for row in rows:
            data.append({
                'Дата_рассылки': row[0],
                'Номер_релиза': row[1],
                'Наименование_клиента': row[2],
                'Основной_контакт': row[3],
                'Копия': row[4]
            })
        return render_template('data_release.html', data=data)
    
    # Обработка запросов и вывод информации из БД
    @app.route('/data_clients/api/clients', methods=['GET'])
    def get_client_info_api():
        try:
            # Используем контекстный менеджер для выполнения операций с БД
            with conn:
                # Получаем все записи из таблицы client_info
                client_infos = list(BMInfo_onClient.select())
            # Преобразуем список записей в список словарей
            results = []
            for client_info in client_infos:
                result = {}
                for column_name in client_info.column_names:
                    result[column_name] = getattr(client_info, column_name)
                results.append(result)
            # Формируем JSON с отступами для улучшения читабельности
            json_data = json.dumps(results, ensure_ascii=False, indent=4)
            # Устанавливаем заголовок Access-Control-Allow-Origin
            response = Response(json_data, content_type='application/json; charset=utf-8')
            response.headers.add('Access-Control-Allow-Origin', '*')
            # Отправляем ответ JSON
            return response
        except Exception as error:
            error_message = {"error": str(error)}
            json_data = json.dumps(error_message, ensure_ascii=False, indent=4)
            response = Response(json_data, content_type='application/json; charset=utf-8')
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

    # Обработка информации, которую получили и записываем её в БД
    @app.route('/data_clients/api/clients', methods=['POST'])
    @require_basic_auth(USERNAME, PASSWORD)
    def post_client_info_api():
        try:
            # Получаем данные из запроса и создаем объекты BMInfo_onClient
            data = request.get_json()
            client_infos = [BMInfo_onClient(**client_data) for client_data in data]

            # Создаем таблицу, если она не существует
            with conn:
                conn.create_tables([BMInfo_onClient])

            # Сохраняем данные в базе данных
            with conn.atomic():
                for client_info in client_infos:
                    client_info.save()

            return 'Data successfully saved to the database!'

        except peewee.OperationalError as error_message:
            # Обработка исключения при возникновении ошибки подключения к БД
            web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
            print("Ошибка подключения к базе данных SQLite:", error_message)
            return "Ошибка с БД"
        except Exception as error:
            # Обработка остальных исключений
            web_error_logger.error("Ошибка: %s", error)
            print("Ошибка:", error)
            return "Ошибка сервера"

    return app

def create_app():
    """Функция создания приложения ВЭБ-сервера"""
    app = Flask(__name__)
    config_file = Path(__file__).parent / 'Web_Server' / 'web_config.py'
    app.config.from_pyfile(config_file)

    # Регистрация обработчиков для URL 
    app.add_url_rule('/', 'handler_get', handler_get, methods=['GET'])

    # Регистрация обработчиков для URL /create_ticket
    app.add_url_rule('/create_ticket', 'handler_get_create_ticket', handler_get_create_ticket, methods=['GET'])
    app.add_url_rule('/create_ticket', 'handler_post_create_ticket', handler_post_create_ticket, methods=['POST'])

    # Регистрация обработчиков для URL /update_ticket
    app.add_url_rule('/update_ticket', 'handler_get_update_ticket', handler_get_update_ticket, methods=['GET'])
    app.add_url_rule('/update_ticket', 'handler_post_update_ticket', handler_post_update_ticket, methods=['POST'])

    # Регистрация обработчиков для URL /undersponed_ticket
    app.add_url_rule('/undersponed_ticket', 'handler_undersponed_ticket', handler_undersponed_ticket, methods=['POST'])

    # Регистрация обработчиков для URL с узнаванием OAuth яндекса (токена авторизации)
    app.add_url_rule('/yandex_oauth_callback', 'handler_get_yandex_oauth_callback', handler_get_yandex_oauth_callback, methods=['GET'])

    # Регистрация обработчиков для API со списком версий отправки релиза
    app.add_url_rule('/data_release/api/versions', 'api_data_release_versions', api_data_release_versions, methods=['GET'])
    # Регистрация обработчика для API с параметром version в URL
    app.route('/data_release/api/<string:version>', methods=['GET'])(require_basic_auth(USERNAME, PASSWORD)(api_data_release_number))
    # Регистрация обработчиков для URL спика всех отправленных версиях
    app.add_url_rule('/data_release', 'data_release_html', data_release_html, methods=['GET'])

    # Регистрация обработчика для API списка учёта версий клиентов
    app.add_url_rule('/clients_all_info/api/clients', 'get_BM_Info_onClient_api', require_basic_auth(USERNAME, PASSWORD)(get_BM_Info_onClient_api), methods=['GET'])
    app.add_url_rule('/clients_all_info/api/clients', 'post_BM_Info_onClient_api', require_basic_auth(USERNAME, PASSWORD)(post_BM_Info_onClient_api), methods=['POST'])
    app.add_url_rule('/clients_all_info/api/clients', 'patch_BM_Info_onClient_api', require_basic_auth(USERNAME, PASSWORD)(patch_BM_Info_onClient_api), methods=['PATCH'])
    app.add_url_rule('/clients_all_info/api/clients', 'delete_BM_Info_onClient_api', require_basic_auth(USERNAME, PASSWORD)(delete_BM_Info_onClient_api), methods=['DELETE'])

    # Регистрация обработчика для API списка карточек клиента
    app.add_url_rule('/clients_all_info/api/clients_card', 'get_client_card_api', require_basic_auth(USERNAME, PASSWORD)(get_client_card_api), methods=['GET'])
    # Регистрация обработчика для API с параметром id в URL
    app.route('/clients_all_info/api/client_card/<int:id>', methods=['GET'])(require_basic_auth(USERNAME, PASSWORD)(get_client_by_id))
    app.add_url_rule('/clients_all_info/api/clients_card', 'post_client_card_api', require_basic_auth(USERNAME, PASSWORD)(post_client_card_api), methods=['POST'])
    app.route('/clients_all_info/api/client_card/<int:id>', methods=['POST'])(require_basic_auth(USERNAME, PASSWORD)(post_client_card_api_by_id))
    app.route('/clients_all_info/api/client_card/<int:id>', methods=['PATCH'])(require_basic_auth(USERNAME, PASSWORD)(patch_client_card_api))
    app.add_url_rule('/clients_all_info/api/clients_card', 'delete_client_card_api', require_basic_auth(USERNAME, PASSWORD)(delete_client_card_api), methods=['DELETE'])

    # Регистрация обработчика для API списка контакта клиента
    #app.add_url_rule('/clients_all_info/api/contacts_card', 'get_contacts_api', require_basic_auth(USERNAME, PASSWORD)(get_contacts_api), methods=['GET'])
    app.route('/clients_all_info/api/contact_card/<int:id>', methods=['GET'])(require_basic_auth(USERNAME, PASSWORD)(get_contact_by_client_id))
    #app.add_url_rule('/clients_all_info/api/contacts_card', 'post_contacts_api', require_basic_auth(USERNAME, PASSWORD)(post_contacts_api), methods=['POST'])
    app.route('/clients_all_info/api/contact_card/<int:id>', methods=['POST'])(require_basic_auth(USERNAME, PASSWORD)(post_contact_api_by_id))
    
    # Регистрация обработчика для API информации по подключению к клиенту
    app.add_url_rule('/clients_all_info/api/connect_info', 'get_connect_info_api', require_basic_auth(USERNAME, PASSWORD)(get_connect_info_api), methods=['GET'])
    app.route('/clients_all_info/api/connect_info/<int:id>', methods=['GET'])(require_basic_auth(USERNAME, PASSWORD)(get_connect_info_by_id))
    app.add_url_rule('/clients_all_info/api/connect_info', 'post_connect_info_api', require_basic_auth(USERNAME, PASSWORD)(post_connect_info_api), methods=['POST'])
    app.route('/clients_all_info/api/connect_info/<int:id>', methods=['PATCH'])(require_basic_auth(USERNAME, PASSWORD)(patch_connect_info_api))
    app.route('/clients_all_info/api/connect_info/<int:id>', methods=['DELETE'])(require_basic_auth(USERNAME, PASSWORD)(delete_connect_info_api))

    # Регистрация обработчика для API информация о серверах клиента
    app.add_url_rule('/clients_all_info/api/bm_servers_card/<int:client_id>', 'get_bm_servers_card_api', require_basic_auth(USERNAME, PASSWORD)(get_bm_servers_card_api), methods=['GET'])
    app.add_url_rule('/clients_all_info/api/bm_servers_card/<int:client_id>', 'post_bm_servers_card_api', require_basic_auth(USERNAME, PASSWORD)(post_bm_servers_card_api), methods=['POST'])

    
    app.add_url_rule('/clients_all_info/api/integration/<int:client_id>', 'get_integration_api', require_basic_auth(USERNAME, PASSWORD)(get_integration_api), methods=['GET'])
    app.add_url_rule('/clients_all_info/api/integration/<int:client_id>', 'post_integration_api', require_basic_auth(USERNAME, PASSWORD)(post_integration_api), methods=['POST'])
    
    return app

if __name__ == '__main__':
    try:
        server_address = ('0.0.0.0', 3030)
        app = create_app()
        web_info_logger.info('Сервер запущен. Порт работы: %s', server_address[1])
        app.run(host=server_address[0], port=server_address[1], debug=True)
    except Exception as error_message:
        web_error_logger.error("Ошибка при запуске ВЭБ-сервера: %s", error_message)
        raise error_message
