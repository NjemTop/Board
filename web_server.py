import json
import logging
from flask import Flask, request
from flask import Response
import xml.etree.ElementTree as ET
from telegram_bot import send_telegram_message

# Создание объекта логгера для ошибок и критических событий
error_logger = logging.getLogger(__name__)
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler('./logs/web-errors.log')
error_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
error_handler.setFormatter(formatter)
error_logger.addHandler(error_handler)

# Создание объекта логгера для информационных сообщений
info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)
info_handler = logging.FileHandler('./logs/web-info.log')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)
info_logger.addHandler(info_handler)

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"

def get_app():
    """Функция приложения ВЭБ-сервера"""
    app = Flask(__name__)

    @app.route('/', methods=['GET'])
    def handle_get():
        """Функция обработки вэбхуков из HappyFox"""
        ip_address = f"Request from {request.remote_addr}: {request.url}"
        user_agent = request.headers.get('User-Agent')
        user_who = f'User-Agent: {user_agent}'
        info_logger.info('Кто-то зашёл на сайт c IP-адреса: %s', ip_address)
        info_logger.info('Его данные подключения: %s', (user_who,))
        return Response('Чё пришёл сюда?', mimetype='text/plain')
    
    @app.route('/create_ticket', methods=['GET'])
    def handle_get_create_ticket():
        """Функция обработки вэбхуков из HappyFox"""
        ip_address = f"Request from {request.remote_addr}: {request.url}"
        user_agent = request.headers.get('User-Agent')
        user_who = f'User-Agent: {user_agent}'
        info_logger.info('Кто-то зашёл на сайт c IP-адреса: %s', ip_address)
        info_logger.info('Его данные подключения: %s', (user_who,))
        return Response('Этот URL для получение вэбхуков(создание)', mimetype='text/plain')
    
    @app.route('/create_ticket', methods=['POST'])
    def create_ticket():
        """Функция обработки создания тикета из HappyFox"""
        message = ""
        message = request.data.decode('utf-8')
        try:
            # находим JSON в сообщении
            json_start = message.find('{')
            if json_start != -1:
                json_str = message[json_start:]
                print('--'*60)
                # парсим JSON
                json_data = json.loads(json_str)
                # находим значения для ключей
                ticket_id = json_data.get("ticket_id")
                subject = json_data.get("subject")
                priority_name = json_data.get("priority_name")
                agent_ticket_url = json_data.get("agent_ticket_url")
                print('**'*60)
                # отправляем сообщение в телеграм-бот
                ticket_message = (f"Новый тикет: {ticket_id}\nТема: {subject}\nПриоритет: {priority_name}\nСсылка: {agent_ticket_url}")
                print(ticket_message)
                # открываем файл и загружаем данные
                with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                # извлекаем значения GROUP_ALERT_NEW_TICKET из SEND_ALERT
                alert_chat_id = data['SEND_ALERT']['GROUP_ALERT_NEW_TICKET']
                send_telegram_message(alert_chat_id, ticket_message)
                info_logger.info('Отправлена следующая информация в группу: %s', 'Новый тикет: {ticket_id}Тема: {subject}Приоритет: {priority_name}Ссылка: {agent_ticket_url}')
            else:
                print('JSON не найден в сообщении.')
                error_logger.error("JSON не найден в сообщении. %s")
                return 'JSON не найден в сообщении.', 400
        except ValueError as e:
            print('Не удалось распарсить JSON в запросе.')
            error_logger.error("Не удалось распарсить JSON в запросе. %s")
            return 'Не удалось распарсить JSON в запросе.', 400
        
        return "OK", 200

    @app.route('/update_ticket', methods=['GET'])
    def handle_get_update_ticket():
        """Функция обработки вэбхуков из HappyFox"""
        ip_address = f"Request from {request.remote_addr}: {request.url}"
        user_agent = request.headers.get('User-Agent')
        user_who = f'User-Agent: {user_agent}'
        info_logger.info('Кто-то зашёл на сайт c IP-адреса: %s', ip_address)
        info_logger.info('Его данные подключения: %s', (user_who,))
        return Response('Этот URL для получение вэбхуков (обнова)', mimetype='text/plain')
    
    @app.route('/update_ticket', methods=['POST'])
    def update_ticket():
        """Функция обработки обновления тикета из HappyFox"""
        message = ""
        message = request.data.decode('utf-8')
        try:
            # проверяем наличие JSON в сообщении
            if '{' not in message:
                print('JSON не найден в сообщении.')
                error_logger.error("JSON не найден в сообщении. %s")
                return 'JSON не найден в сообщении.', 400
            # находим JSON в сообщении
            json_start = message.find('{')
            if json_start != -1:
                json_str = message[json_start:]
                print('--'*60)
                # парсим JSON
                try:
                    json_data = json.loads(json_str)
                except json.decoder.JSONDecodeError:
                    print('Не удаётся распарсить JSON в запросе.')
                    error_logger.error("Не удаётся распарсить JSON в запросе. %s")
                    return 'Не удаётся распарсить JSON в запросе.', 400
                # находим значения кто ответил
                json_message_type = json_data.get("update", {}).get("message_type")
                # если ответ был дан со стороны клиента
                if json_message_type == "Client Reply":
                    # находим значения для ключей
                    ticket_id = json_data.get("ticket_id")
                    subject = json_data.get("subject")
                    priority_name = json_data.get("priority_name")
                    assignee_name = json_data.get("assignee_name")
                    client_name = json_data['client_details']['name']
                    agent_ticket_url = json_data.get("agent_ticket_url")
                    print('**'*60)
                    # Формируем сообщение в текст отправки
                    ticket_message = (f"Новое сообщение в тикете: {ticket_id}\nТема: {subject}\nИмя клиента: {client_name}\nПриоритет: {priority_name}\nНазначен: {assignee_name}\nСсылка: {agent_ticket_url}")
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
                        if hf.find('name').text == assignee_name:
                            # Если значения совпадают, сохраняем значение элемента chat_id в alert_chat_id
                            alert_chat_id = hf.find('chat_id').text
                            break  # Выходим из цикла, т.к. нужный элемент уже найден

                    # Если alert_chat_id не был найден, выводим ошибку
                    if alert_chat_id is None:
                        print(f"Не удалось найти chat_id для пользователя {assignee_name}.")
                        error_logger.error("Не удалось найти 'chat_id' для пользователя %s", assignee_name)
                    else:
                        # Отправляем сообщение в телеграм-бот
                        send_telegram_message(alert_chat_id, ticket_message)
                    info_logger.info('Отправлена следующая информация в группу: %s', f'Новое сообщение в тикете: {ticket_id} Тема: {subject} Приоритет: {priority_name} Имя клиента: {client_name} Назначен: {assignee_name} Ссылка: {agent_ticket_url}')
                    # Отправляем ответ о том, что всё принято и всё хорошо
                    return "OK", 200
                # если было изменение назначенного на тикет
                elif json_data.get("update", {}).get("assignee_change") is not None:
                    try:
                        # находим значения для ключей
                        who_change = json_data["update"]["by"]["name"]
                        new_assignee_name = json_data["update"]["assignee_change"]["new"]
                        ticket_id = json_data.get("ticket_id")
                        subject = json_data.get("subject")
                        priority_name = json_data.get("priority_name")
                        agent_ticket_url = json_data.get("agent_ticket_url")
                        # Формируем сообщение в текст отправки
                        new_assignee_name_message = (f"Сотрудником: {who_change}\nИзменил назначенного в тикете: {ticket_id}\nТема: {subject}\nИмя клиента: {client_name}\nПриоритет: {priority_name}\nСсылка: {agent_ticket_url}")
                        # Разбор XML-файла и получение корневого элемента
                        tree = ET.parse('data.xml')
                        root = tree.getroot()
                        # Находим все элементы header_footer внутри элемента user
                        header_footer_elements = root.findall('.//user/header_footer')
                        # Задаем начальное значение alert_chat_id
                        alert_chat_id = None
                        try:
                            # Проходим циклом по всем найденным элементам header_footer
                            for hf in header_footer_elements:
                                # Сравниваем значение элемента name с new_assignee_name_message
                                if hf.find('name').text == new_assignee_name:
                                    # Если значения совпадают, сохраняем значение элемента chat_id в alert_chat_id
                                    alert_chat_id = hf.find('chat_id').text
                                    break  # Выходим из цикла, т.к. нужный элемент уже найден
                        except AttributeError as e:
                            print(f"Ошибка при обработке xml-файла: 'chat_id' не найден для пользователя {new_assignee_name_message}.")
                            error_logger.error("Ошибка при обработке xml-файла: 'chat_id' не найден для пользователя %s. Ошибка: %s", new_assignee_name_message, e)
                        # Если alert_chat_id не был найден, выводим ошибку
                        if alert_chat_id is None:
                            print(f"Не удалось найти chat_id для пользователя {new_assignee_name_message}.")
                            error_logger.error("Не удалось найти 'chat id' для пользователя %s", new_assignee_name_message)
                        else:
                            # Отправляем сообщение в телеграм-бот
                            send_telegram_message(alert_chat_id, new_assignee_name_message)
                        info_logger.info('Отправлена следующая информация в группу: %s', f'Сотрудник: {who_change} изменил назначенного в тикете: {ticket_id} Тема: {subject} Приоритет: {priority_name} Имя клиента: {client_name} Назначен: {new_assignee_name_message} Ссылка: {agent_ticket_url}')
                        # Отправляем ответ о том, что всё принято и всё хорошо
                        return "OK", 200
                    except Exception as e:
                        error_logger.error("Не удалось собрать инфорамацию из запроса, который прислал HappyFox %s", e)
                else:
                    # Отправляем ответ о том, что приняли файлы, однако не нашли полезной информации, но приняли же
                    return "OK", 200
            else:
                print('JSON не найден в сообщении.')
                error_logger.error("JSON не найден в сообщении. %s")
                return 'JSON не найден в сообщении.', 400
        except ValueError as e:
            print('Не удалось распарсить JSON в запросе.')
            error_logger.error("Не удалось распарсить JSON в запросе. %s", e)
            return 'Не удалось распарсить JSON в запросе.', 400

    return app

def run_server():
    """Функция запуска ВЕБ-СЕРВЕРА для прослушивания вебхуков. Алерты"""
    try:
        server_address = ('0.0.0.0', 3030)
        app = get_app()
        info_logger.info('Сервер запущен на порту %s', server_address[1])
        app.run(host=server_address[0], port=server_address[1], debug=True)
    except Exception as e:
        error_logger.error("Ошибка при запуске ВЭБ-сервера: %s", e)
        raise e

run_server()