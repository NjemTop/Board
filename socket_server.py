"""Модуль сокета, через которое работает ВЭБ-приложение"""
import socket
import json
import logging
import subprocess
from telegram_bot import send_telegram_message

# Создание объекта логгера для ошибок и критических событий
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
# создаем обработчик, который будет записывать ошибки в файл Web-error.log
error_handler = logging.FileHandler('Web-errors.log')
error_handler.setLevel(logging.ERROR)
# создаем форматирование
error_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M'))
# добавляем обработчик в логгер
error_logger.addHandler(error_handler)

# Создание объекта логгера для информационных сообщений
info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)
info_handler = logging.FileHandler('web-info.log')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M'))
info_logger.addHandler(info_handler)

# создаемTCP/IP сокет
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Привязываем сокет к порту
try:
    server_address = ('', 3030)
    print(f'Старт сервера на порт {server_address}')
    info_logger.info('Старт сервера на порт %s', server_address)
    sock.bind(server_address)
except socket.error as e:
    error_logger.error("Ошибка при запуске ВЭБ-сервера: %s", e)
    raise e

# Слушаем входящие подключения
sock.listen(1)
# Чат айди, куда отправляем алерты
alert_chat_id = -784493618

while True:
    # ждем соединения
    print('Ожидание соединения...')
    info_logger.info('Ожидание соединения...')
    connection, client_address = sock.accept()
    message = ""
    messages_received = 0
    try:
        print('Подключено к:', client_address)
        # Принимаем данные порциями и ретранслируем их
        while True:
            data = connection.recv(8192)
            if not data:
                print('Нет данных от:', client_address)
                info_logger.info('Нет данных от: %s', client_address)
                break
            # кодируем строку с русскими символами
            message += data.decode('utf-8')
            try:
                # находим JSON в сообщении
                json_start = message.find('{')
                if json_start != -1:
                    json_str = message[json_start:]
                    print('--'*60)
                    # парсим JSON
                    json_data = json.loads(json_str)
                    print(f'ПАРСИНГ JSON: {json_data}')
                    info_logger.info('ПАРСИНГ JSON: %s', json_data)
                    # находим значения для ключей "ticket_id", "subject", "priority_name" и "agent_ticket_url"
                    ticket_id = json_data.get("ticket_id")
                    subject = json_data.get("subject")
                    priority_name = json_data.get("priority_name")
                    agent_ticket_url = json_data.get("agent_ticket_url")
                    print('**'*60)
                    # отправляем сообщение в телеграм-бот
                    ticket_message = (f"Новый тикет: {ticket_id}\nТема: {subject}\nПриоритет: {priority_name}\nСсылка: {agent_ticket_url}")
                    send_telegram_message(alert_chat_id, ticket_message)
                    # отправляем данные обратно клиенту
                    response = message.upper().encode()
                    print('Отправка обратно клиенту.')
                    connection.sendall(response)
                    message = ""
                else:
                    print('JSON не найден в сообщении.')
                    info_logger.info('JSON не найден в сообщении.')
            except json.decoder.JSONDecodeError:
                print('Не удалось распарсить JSON в запросе.')
                continue

    finally:
        # Очищаем соединение
        connection.close()
