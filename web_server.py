import json
import logging
from flask import Flask, request
from telegram_bot import send_telegram_message

# Создание объекта логгера для ошибок и критических событий
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler('web-errors.log')
error_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
error_handler.setFormatter(formatter)
error_logger.addHandler(error_handler)

# Создание объекта логгера для информационных сообщений
info_logger = logging.getLogger('info_logger')
info_logger.setLevel(logging.INFO)
info_handler = logging.FileHandler('web-info.log')
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)
info_logger.addHandler(info_handler)

def get_app():
    """Функция приложения ВЭБ-сервера"""
    app = Flask(__name__)

    @app.route('/', methods=['POST'])
    def handle_ticket():
        """Функция обработки вэбхуков из HappyFox"""
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
                # Чат айди, куда отправляем алерты
                alert_chat_id = -1001760725213
                send_telegram_message(alert_chat_id, ticket_message)
                info_logger.info('Отправлена следующая информация в группу: %s', ticket_message)
            else:
                print('JSON не найден в сообщении.')
                error_logger.error("JSON не найден в сообщении. %s")
        except json.decoder.JSONDecodeError:
            print('Не удалось распарсить JSON в запросе.')
            error_logger.error("Не удалось распарсить JSON в запросе. %s")
            return 'Не удалось распарсить JSON в запросе.', 400

        return "OK", 200
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
