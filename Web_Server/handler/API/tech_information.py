from flask import request, Response, jsonify
import logging
import json
import peewee
import traceback
from DataBase.model_class import BMInfo_onClient, TechInformation, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def get_tech_information(client_id):
    """Функция возвращает информацию о технических данных для клиента с указанным client_id."""
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

            # Получаем техническую информацию для данного клиента
            try:
                tech_info = TechInformation.get(TechInformation.tech_information_id == client.technical_information)
            except peewee.DoesNotExist:
                message = f"Техническая информация для клиента с ID {client_id} не найдена"
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            # Возвращаем техническую информацию в виде словаря
            tech_info_data = {
                'id': tech_info.id,
                'tech_information_id': tech_info.tech_information_id.id,
                'Версия_сервера': tech_info.server_version,
                'Дата_обновления': tech_info.update_date,
                'API': tech_info.api,
                'iPad': tech_info.ipad,
                'Andriod': tech_info.android,
                'MDM': tech_info.mdm,
                'Локализация Web': tech_info.localizable_web,
                'Локализация iOS': tech_info.localizable_ios,
                'Скины Web': tech_info.skins_web,
                'Скины iOS': tech_info.skins_ios
            }

        json_data = json.dumps(tech_info_data, ensure_ascii=False, indent=4)
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
       
def post_tech_information(client_id):
    # Проверяем существование клиента с указанным client_id
    try:
        with conn:
            client = BMInfo_onClient.get(BMInfo_onClient.client_info == client_id)
    except peewee.DoesNotExist:
        return {'error': f'Client with client_id {client_id} not found'}, 404

    # Получаем данные из JSON-запроса
    data = request.get_json()

    # Проверяем наличие обязательных полей 'Версия_сервера' и 'Дата_обновления' в данных запроса
    if 'Версия_сервера' not in data or 'Дата_обновления' not in data:
        return {'error': "Fields 'Версия_сервера' and 'Дата_обновления' are required"}, 400

    # Извлекаем значения полей из данных запроса
    server_version = data['Версия_сервера']
    update_date = data['Дата_обновления']

    # Проверяем, что значения 'Версия_сервера' и 'Дата_обновления' являются строками и не пустыми
    if not (isinstance(server_version, str) and isinstance(update_date, str) and server_version and update_date):
        return {'error': "Fields 'Версия_сервера' and 'Дата_обновления' must be non-empty strings"}, 400

    # Создаем словарь с необязательными полями
    optional_fields = {key: data.get(key, None) for key in TechInformation.COLUMN_NAMES if key not in ['Версия_сервера', 'Дата_обновления']}

    # Создаем новую запись в таблице TechInformation и сохраняем ее в базе данных
    try:
        tech_info = TechInformation.create(tech_information_id=client.technical_information, server_version=server_version, update_date=update_date, **optional_fields)
        tech_info.save()
    except Exception as error_message:
        return {'error': f'Error creating tech information: {str(error_message)}'}, 500

    # Возвращаем сообщение об успешном создании записи
    return {'message': 'Tech information created successfully'}, 201
