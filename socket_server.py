"""Модуль сокета, через которое работает ВЭБ-приложение"""
import socket
import json
from telegram_bot import send_telegram_message

# создаемTCP/IP сокет
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Привязываем сокет к порту
server_address = ('', 3030)
print(f'Старт сервера на порт {server_address}')
sock.bind(server_address)

# Слушаем входящие подключения
sock.listen(1)

alert_chat_id = -784493618

while True:
    # ждем соединения
    print('Ожидание соединения...')
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
            except json.decoder.JSONDecodeError:
                print('Не удалось распарсить JSON в запросе.')
                continue

    finally:
        # Очищаем соединение
        connection.close()
