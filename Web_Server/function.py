import json
import logging
import xml.etree.ElementTree as ET
from Web_Server.web_config import CONFIG_FILE
from System_func.send_telegram_message import Alert
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

# Создаем объект класса Alert
alert = Alert()

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
