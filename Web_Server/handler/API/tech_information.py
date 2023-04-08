from flask import request, Response, jsonify
import logging
import json
import peewee
import traceback
from datetime import datetime
from DataBase.model_class import BMInfo_onClient, TechInformation, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def get_all_tech_information():
    try:
        with conn:
            # Получаем все записи из таблицы BMInfo_onClient
            clients = BMInfo_onClient.select()

            # Создаем список для хранения результатов
            result = []

            for client in clients:
                # Получаем соответствующую техническую информацию из таблицы TechInformation
                tech_infos = TechInformation.select().where(TechInformation.tech_information_id == client.technical_information)

                # Создаем список для хранения информации о технических данных
                tech_infos_data = []

                for tech_info in tech_infos:
                    tech_info_data = {
                        'id': tech_info.id,
                        'tech_information_id': tech_info.tech_information_id.id,
                        'server_version': tech_info.server_version,
                        'update_date': tech_info.update_date,
                        'api': tech_info.api,
                        'ipad': tech_info.ipad,
                        'android': tech_info.android,
                        'mdm': tech_info.mdm,
                        'localizable_web': tech_info.localizable_web,
                        'localizable_ios': tech_info.localizable_ios,
                        'skins_web': tech_info.skins_web,
                        'skins_ios': tech_info.skins_ios
                    }
                    tech_infos_data.append(tech_info_data)

                # Добавляем информацию о клиенте и его технических данных в результат
                client_data = {
                    'client_id': client.client_info,
                    'client_name': client.client_name,
                    'tech_information': tech_infos_data
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
                'server_version': tech_info.server_version,
                'update_date': tech_info.update_date,
                'api': tech_info.api,
                'ipad': tech_info.ipad,
                'android': tech_info.android,
                'mdm': tech_info.mdm,
                'localizable_web': tech_info.localizable_web,
                'localizable_ios': tech_info.localizable_ios,
                'skins_web': tech_info.skins_web,
                'skins_ios': tech_info.skins_ios
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
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
       
def post_tech_information(client_id):
    # Проверяем существование клиента с указанным client_id
    try:
        with conn:
            client = BMInfo_onClient.get(BMInfo_onClient.client_info == client_id)
    except peewee.DoesNotExist:
        return {'error': f'Клиент с client_id {client_id} не найден'}, 404

    # Получаем данные из JSON-запроса
    data = request.get_json()

    # Проверяем наличие обязательных полей 'server_version' и 'update_date' в данных запроса
    if 'server_version' not in data or 'update_date' not in data:
        return {'error': "Поля 'server_version' и 'update_date' обязательны"}, 400

    # Извлекаем значения полей из данных запроса
    server_version = data['server_version']
    update_date_str = data['update_date']

    # Проверяем, что значение 'server_version' является строкой и не пустое
    if not (isinstance(server_version, str) and server_version):
        return {'error': "Поля 'server_version' и 'update_date' должны быть непустыми строками"}, 400

    # Проверяем, что значение 'update_date' является корректной датой
    try:
        update_date = datetime.strptime(update_date_str, '%d-%m-%Y').date()
    except ValueError:
        return {'error': "Поле 'update_date' должно быть корректной датой в формате 'DD-MM-YYYY'"}, 400

    # Создаем словарь с необязательными полями
    optional_fields = {key: data.get(key, None) for key in TechInformation.COLUMN_NAMES if key not in ['server_version', 'update_date']}

    # Проверяем корректность типов данных для всех ключей
    for key, value in optional_fields.items():
        if value is not None:
            if key in ['api', 'localizable_web', 'localizable_ios', 'skins_web', 'skins_ios']:
                if not isinstance(value, bool):
                    return {'error': f"Поле '{key}' должно быть булевым типом"}, 400
            else:
                if not isinstance(value, str):
                    return {'error': f"Поле '{key}' должно быть строкой"}, 400

    # Создаем новую запись в таблице TechInformation и сохраняем ее в базе данных
    try:
        tech_info = TechInformation.create(tech_information_id=client.technical_information, server_version=server_version, update_date=update_date, **optional_fields)
        tech_info.save()
    except Exception as error_message:
        return {'error': f'Ошибка при создании технической информации: {str(error_message)}'}, 500

    # Возвращаем сообщение об успешном создании записи
    return {'message': 'Техническая информация успешно создана'}, 201