from flask import request, Response, jsonify
import logging
import json
import peewee
from DataBase.model_class import BMInfo_onClient, Integration, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def get_integration_api(client_id):
    try:
        with conn:
            # Получаем запись клиента с указанным ID
            client = BMInfo_onClient.get(BMInfo_onClient.client_info == client_id)
    except peewee.DoesNotExist:
        # Если запись клиента не найдена, возвращаем ошибку 404
        return jsonify({'error': f'Клиент с ID {client_id} не найден'}), 404

    # Получаем integration_id из найденной записи клиента
    integration_id = client.integration

    try:
        with conn:
            # Получаем запись интеграции с указанным integration_id
            integration = Integration.get(Integration.integration_id == integration_id)
    except peewee.DoesNotExist:
        # Если запись интеграции не найдена, возвращаем ошибку 404
        return jsonify({'error': f'Нет данных об интеграции клиента {client_id}'}), 404

    # Создаем словарь для хранения данных интеграции
    integration_data = {}

    # Итерируемся по столбцам таблицы Integration и добавляем значения в словарь
    for column_name in Integration.COLUMN_NAMES:
        # Пропускаем столбец "integration_id"
        if column_name == 'integration_id':
            continue

        value = getattr(integration, column_name)
        # Если значение равно None, устанавливаем его в False
        if value is None:
            value = False
        integration_data[column_name] = value

    # Возвращаем данные интеграции в формате JSON с отступами для лучшей читаемости
    response = Response(json.dumps(integration_data, indent=2), content_type='application/json; charset=utf-8')
    response.headers.add('Cache-Control', 'no-store')
    response.headers.add('Pragma', 'no-cache')
    return response, 200

def post_integration_api(client_id):
    try:
        with conn:
            # Получаем запись клиента с указанным ID
            client = BMInfo_onClient.get(BMInfo_onClient.client_info == client_id)
    except peewee.DoesNotExist:
        # Если запись клиента не найдена, возвращаем ошибку 404
        return jsonify({'error': 'Клиент с ID {client_id} не найден'}), 404

    # Получаем integration_id из найденной записи клиента
    integration_id = client.integration

    # Получаем данные из POST-запроса
    data = request.json

    # Проверяем, что входные данные являются словарем
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid input data. Expected a JSON object'}), 400

    # Проверяем, что в словаре data только допустимые ключи
    allowed_keys = set(Integration.COLUMN_NAMES) - {'integration_id'}
    for key in data:
        if key not in allowed_keys:
            return jsonify({'error': f'Invalid key: {key}. Allowed keys are: {", ".join(allowed_keys)}'}), 400

    # Проверяем, что значения в словаре data имеют допустимый тип (bool)
    for key, value in data.items():
        if not isinstance(value, bool):
            return jsonify({'error': f'Invalid value for key {key}. Expected a boolean value'}), 400
        
    # Создаем словарь с значениями по умолчанию
    default_data = {key: False for key in Integration.COLUMN_NAMES}
    default_data['integration_id'] = integration_id

    # Обновляем значения по умолчанию данными из POST-запроса
    default_data.update(data)

    try:
        with conn:
            # Создаем запись интеграции в таблице Integration с полученными данными
            integration = Integration.create(**default_data)
    except peewee.IntegrityError:
        # Если запись с таким integration_id уже существует, возвращаем ошибку 409
        return jsonify({'error': 'Integration already exists'}), 409

    # Возвращаем сообщение об успешном создании записи интеграции
    return jsonify({'message': 'Integration created successfully'}), 201

def patch_integration_api(client_id):
    try:
        with conn:
            # Получаем запись клиента с указанным ID
            client = BMInfo_onClient.get(BMInfo_onClient.client_info == client_id)
    except peewee.DoesNotExist:
        # Если запись клиента не найдена, возвращаем ошибку 404
        return jsonify({'error': f'Клиент с ID {client_id} не найден'}), 404

    # Получаем integration_id из найденной записи клиента
    integration_id = client.integration

    try:
        with conn:
            # Получаем запись интеграции с указанным integration_id
            integration = Integration.get(Integration.integration_id == integration_id)
    except peewee.DoesNotExist:
        # Если запись интеграции не найдена, возвращаем ошибку 404
        return jsonify({'error': 'Нет данных об интеграции'}), 404

    # Получаем данные из PATCH-запроса
    patch_data = request.json

    # Проверяем, что полученные данные являются словарем
    if not isinstance(patch_data, dict):
        return jsonify({'error': 'Неверный формат данных'}), 400

    # Итерируемся по столбцам таблицы Integration, исключая столбец "integration_id"
    for column_name in (column for column in Integration.COLUMN_NAMES if column != 'integration_id'):
        # Если столбец присутствует в patch_data, обновляем значение в записи интеграции
        if column_name in patch_data:
            value = patch_data[column_name]

            # Проверяем, что значение является булевым
            if not isinstance(value, bool):
                return jsonify({'error': f'Неверный тип данных для столбца {column_name}'}), 400

            setattr(integration, column_name, value)

    try:
        with conn:
            # Сохраняем обновленную запись интеграции в базе данных
            integration.save()
    except Exception as e:
        # Если возникла ошибка при сохранении, возвращаем ошибку 500
        return jsonify({'error': f'Ошибка при обновлении данных интеграции: {e}'}), 500

    # Возвращаем успешный ответ
    return jsonify({'message': 'Данные интеграции успешно обновлены'}), 200
