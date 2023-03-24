import json
import logging
import requests
from functools import wraps
from werkzeug.security import check_password_hash
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash
from flask import Response
from flask import render_template
import sqlite3
import xml.etree.ElementTree as ET
from telegram_bot import send_telegram_message

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
# Создание объекта логгера для ошибок и критических событий
web_error_logger = logging.getLogger('WebError')
web_error_logger.setLevel(logging.ERROR)
web_error_handler = logging.FileHandler('./logs/web-errors.log')
web_error_handler.setLevel(logging.ERROR)
web_error_handler.setFormatter(formatter)
web_error_logger.addHandler(web_error_handler)

# Создание объекта логгера для информационных сообщений
web_info_logger = logging.getLogger('WebInfo')
web_info_logger.setLevel(logging.INFO)
web_info_handler = logging.FileHandler('./logs/web-info.log')
web_info_handler.setLevel(logging.INFO)
web_info_handler.setFormatter(formatter)
web_info_logger.addHandler(web_info_handler)

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"

USERNAME = 'Njem'
PASSWORD = generate_password_hash('Rfnzkj123123')

# Создаем функцию-декоратор для аутентификации Basic Auth
def require_basic_auth(username, password):
    """Функция-декоратор принимает исходную функцию (представление) в качестве аргумента"""
    def decorator(f):
        # Используем wraps, чтобы сохранить метаданные исходной функции
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Получаем объект аутентификации из запроса
            auth = request.authorization

            # Проверяем, что аутентификация предоставлена и что имя пользователя и пароль верны
            if auth and auth.username == username and check_password_hash(password, auth.password):
                # Если аутентификация прошла успешно, выполняем исходную функцию
                return f(*args, **kwargs)
            else:
                # Если аутентификация не удалась, возвращаем ошибку 401 и заголовок WWW-Authenticate
                return Response('Authorization required', 401, {'WWW-Authenticate': 'Basic realm="Login required"'})
        
        # Возвращаем функцию, обернутую декоратором
        return decorated_function

    # Возвращаем функцию-декоратор
    return decorator

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
        send_telegram_message(alert_chat_id, ticket_message)
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
            send_telegram_message(alert_chat_id, new_assignee_name_message)
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
                send_telegram_message(alert_chat_id, ping_ticket_message)
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
                send_telegram_message(alert_chat_id, ping_ticket_message)
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
                send_telegram_message(alert_chat_id, ping_ticket_message)
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
        send_telegram_message(alert_chat_id, ticket_message)
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
        conn = sqlite3.connect('./DataBase/database.db')
        cur = conn.cursor()
        # Получение списка всех номеров релизов и дат создания
        cur.execute('SELECT DISTINCT Дата_рассылки, Номер_релиза FROM info')
        rows = cur.fetchall()
        conn.close()
        # Сформировать список словарей с ключами "Data" и "Number"
        versions = [{'Data': row[0], 'Number': row[1]} for row in rows]
        # Формирование JSON с отступами для улучшения читабельности
        json_data = json.dumps(versions, ensure_ascii=False, indent=4)
        # Установка заголовка Access-Control-Allow-Origin
        response = Response(json_data, content_type='application/json; charset=utf-8')
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправка ответа JSON
        return response

    # Определение маршрута для API с аргументом 'version' в URL
    @app.route('/data_release/api/<string:version>', methods=['GET'])
    # Применение декоратора require_basic_auth для аутентификации пользователей
    @require_basic_auth(USERNAME, PASSWORD)
    def api_data_release(version):
        """Функция просмотра контактов, кому ушла рассылка через API"""
        # Подключение к базе данных SQLite
        conn = sqlite3.connect('./DataBase/database.db')
        cur = conn.cursor()
        # Фильтрация данных по номеру релиза
        cur.execute('SELECT * FROM info WHERE Номер_релиза = ?', (version,))
        rows = cur.fetchall()
        # Закрытие соединения с базой данных
        conn.close()
        data = []
        # Преобразование полученных данных в список словарей
        for row in rows:
            contacts = {
                'Main': row[3],
                'Copy': row[4]
            }
            data.append({
                'Data': row[0],
                'Number': row[1],
                'Client': row[2],
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
    
    @app.route('/data_release', methods=['GET'])
    def data_release_html():
        """Функция вывода информации об рассылке в HTML странице"""
        release_number = request.args.get('release_number', 'all')
        conn = sqlite3.connect('./DataBase/database.db')
        cur = conn.cursor()
        if release_number == 'all':
            cur.execute('SELECT * FROM info')
        else:
            cur.execute('SELECT * FROM info WHERE "Номер_релиза" = ?', (release_number,))
        rows = cur.fetchall()
        conn.close()
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
        
    return app

def run_server():
    """Функция запуска ВЕБ-СЕРВЕРА для прослушивания вебхуков. Алерты"""
    try:
        server_address = ('0.0.0.0', 3030)
        app = get_app()
        web_info_logger.info('Сервер запущен на порту %s', server_address[1])
        app.run(host=server_address[0], port=server_address[1], debug=True)
    except Exception as error_message:
        web_error_logger.error("Ошибка при запуске ВЭБ-сервера: %s", error_message)
        raise error_message

run_server()