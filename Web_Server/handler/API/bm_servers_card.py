from flask import request, Response, jsonify
import logging
import peewee
import traceback
from DataBase.model_class import ClientsCard, BMServersCard, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

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
