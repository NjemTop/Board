from flask import request, Response, jsonify
import logging
import json
import peewee
import traceback
from DataBase.model_class import BMInfo_onClient, Servise, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def get_all_services():
    try:
        with conn:
            # Получаем все записи из таблицы BMInfo_onClient
            clients = BMInfo_onClient.select()

            # Создаем список для хранения результатов
            result = []

            for client in clients:
                # Получаем соответствующую информацию об услугах из таблицы service
                services = Servise.select().where(Servise.service_id == client.client_info)

                # Создаем список для хранения информации об услугах
                services_data = []

                for service in services:
                    service_data = {
                        'id': service.id,
                        'service_id': service.service_id.client_info,
                        'service_pack': service.service_pack,
                        'manager': service.manager,
                        'loyal': service.loyal
                    }
                    services_data.append(service_data)

                # Добавляем информацию о клиенте и его услугах в результат
                client_data = {
                    'client_id': client.client_info,
                    'client_name': client.client_name,
                    'services': services_data
                }
                result.append(client_data)

        json_data = json.dumps(result, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8')
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except peewee.OperationalError as error_message:
        print("Ошибка подключения к базе данных SQLite:", error_message)
        message = f"Ошибка подключения к базе данных SQLite: {error_message}"
        json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as error:
        print("Ошибка сервера:", error)
        message = f"Ошибка сервера: {error}"
        json_data = json.dumps({"message": message, "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

def get_service(client_id):
    """Функция возвращает информацию об услуге для клиента с указанным client_id."""
    try:
        with conn:
            # Проверяем существование клиента с указанным client_id
            try:
                client = BMInfo_onClient.get(BMInfo_onClient.client_info == client_id)
            except peewee.DoesNotExist:
                message = f"Клиент с ID {client_id} не найден"
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            # Получаем информацию об услуге для данного клиента
            try:
                service = Servise.get(Servise.service_id == client.service)
            except peewee.DoesNotExist:
                message = f"Услуга для клиента с ID {client_id} не найдена"
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            # Возвращаем информацию об услуге в виде словаря
            service_data = {
                'id': service.id,
                'service_id': service.service_id,
                'service_pack': service.service_pack,
                'manager': service.manager,
                'loyal': service.loyal
            }

        json_data = json.dumps(service_data, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8')
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except peewee.OperationalError as error_message:
        print("Ошибка подключения к базе данных SQLite:", error_message)
        message = f"Ошибка подключения к базе данных SQLite: {error_message}"
        json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as error:
        print("Ошибка сервера:", error)
        message = f"Ошибка сервера: {error}"
        json_data = json.dumps({"message": message, "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

def post_service(client_id):
    # Проверяем существование клиента с указанным client_id
    try:
        with conn:
            # Получаем запись клиента с указанным ID
            client = BMInfo_onClient.get(BMInfo_onClient.client_info == client_id)
    except peewee.DoesNotExist:
        return {'error': f'Client with client_id {client_id} not found'}, 404

    # Получаем данные из JSON-запроса
    data = request.get_json()

    # Проверяем наличие обязательных полей 'service_pack' и 'manager' в данных запроса
    if 'service_pack' not in data or 'manager' not in data:
        return {'error': 'Service_pack and manager fields are required'}, 400

    # Извлекаем значения полей из данных запроса
    service_pack = data['service_pack']
    manager = data['manager']
    loyal = data.get('loyal', None)  # Значение по умолчанию для поля 'loyal' равно None

    # Проверяем, что значения 'service_pack' и 'manager' являются строками и не пустыми
    if not (isinstance(service_pack, str) and isinstance(manager, str) and service_pack and manager):
        return {'error': 'Service_pack and manager fields must be non-empty strings'}, 400

    # Если поле 'loyal' присутствует, проверяем, что оно является строкой
    if loyal is not None and not isinstance(loyal, str):
        return {'error': 'Loyal field must be a string'}, 400

    # Создаем новую запись в таблице Servise и сохраняем ее в базе данных
    try:
        service = Servise.create(service_id=client.technical_information, service_pack=service_pack, manager=manager, loyal=loyal)
        service.save()
    except Exception as error_masage:
        return {'error': f'Error creating service: {str(error_masage)}'}, 500

    # Возвращаем сообщение об успешном создании записи
    return {'message': 'Service created successfully'}, 201
