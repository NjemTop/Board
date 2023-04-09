from flask import request, Response, jsonify
import logging
import json
import peewee
from DataBase.model_class import ClientsCard, TechAccount, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def get_tech_account_api(client_id):
    try:
        with conn:
            client = ClientsCard.get(ClientsCard.client_id == client_id)
    except peewee.DoesNotExist:
        return jsonify({'error': f'Клиент с ID {client_id} не найден'}), 404

    tech_account_id = client.tech_account

    # Получаем все записи с указанным tech_account_id
    try:
        with conn:
            tech_accounts = TechAccount.select().where(TechAccount.tech_account_id == tech_account_id)
    except peewee.DoesNotExist:
        return jsonify({'error': 'Нет данных о технических аккаунтах'}), 404

    # Создаем список для хранения данных технических аккаунтов
    tech_accounts_data = []

    # Итерируемся по найденным записям и добавляем их данные в список
    for tech_account in tech_accounts:
        account_data = {column_name: getattr(tech_account, column_name) for column_name in TechAccount.COLUMN_NAMES if column_name != 'tech_account_id'}
        tech_accounts_data.append(account_data)

    # Проверяем, если список результатов пуст
    if not tech_accounts_data:
        return jsonify({'message': f'По текущему клиенту с ID {client_id} информации нет'}), 200

    # Формируем структуру ответа
    response_data = {
        'client_id': client_id,
        'contacts': tech_accounts_data
    }

    # Возвращаем данные технических аккаунтов в формате JSON с отступами для лучшей читаемости и корректным отображением текста на русском языке
    response = Response(json.dumps(response_data, indent=2, ensure_ascii=False), content_type='application/json; charset=utf-8')
    response.headers.add('Cache-Control', 'no-store')
    response.headers.add('Pragma', 'no-cache')
    return response, 200

def post_tech_account_api(client_id):
    # Получаем клиента с указанным client_id
    try:
        with conn:
            client = ClientsCard.get(ClientsCard.client_id == client_id)
    except peewee.DoesNotExist:
        return jsonify({'error': f'Клиент с ID {client_id} не найден'}), 404

    tech_account_id = client.tech_account

    # Получаем данные технического аккаунта из запроса
    tech_account_data = request.json
    if not isinstance(tech_account_data, dict):
        return jsonify({'error': 'Неверный формат данных'}), 400

    # Устанавливаем tech_account_id равным tech_account_id
    tech_account_data['tech_account_id'] = tech_account_id

    # Создаем запись технического аккаунта с полученными данными
    try:
        with conn:
            tech_account = TechAccount.create(**tech_account_data)
    except Exception as e:
        return jsonify({'error': f'Ошибка при создании технического аккаунта: {e}'}), 500

    # Формируем ответ с данными созданного технического аккаунта
    response_data = {column_name: getattr(tech_account, column_name) for column_name in TechAccount.COLUMN_NAMES}
    return jsonify(response_data), 201

def patch_tech_account_api(client_id):
    try:
        with conn:
            client = ClientsCard.get(ClientsCard.client_id == client_id)
    except peewee.DoesNotExist:
        return jsonify({'error': f'Клиент с ID {client_id} не найден'}), 404

    tech_account_id = client.tech_account

    tech_account_data = request.json
    if not isinstance(tech_account_data, dict):
        return jsonify({'error': 'Неверный формат данных'}), 400

    try:
        with conn:
            TechAccount.update(**tech_account_data).where(TechAccount.tech_account_id == tech_account_id).execute()
    except Exception as e:
        return jsonify({'error': f'Ошибка при обновлении технического аккаунта: {e}'}), 500

    return jsonify({'message': 'Технический аккаунт успешно обновлен'}), 200

def delete_tech_account_api(id):
    """Функция удаления технологической записи клиента по ID"""
    # Получаем технический аккаунт с указанным ID
    try:
        with conn:
            tech_account = TechAccount.get(TechAccount.id == id)
    except peewee.DoesNotExist:
        # Возвращаем ошибку, если технический аккаунт не найден
        return jsonify({'error': f'Технический аккаунт с ID {id} не найден'}), 404

    # Удаляем технический аккаунт с указанным ID
    try:
        with conn:
            deleted_rows = TechAccount.delete().where(TechAccount.id == id).execute()
    except Exception as e:
        # Возвращаем ошибку, если возникла ошибка при удалении технического аккаунта
        return jsonify({'error': f'Ошибка при удалении технического аккаунта: {e}'}), 500

    # Проверяем, был ли удален технический аккаунт
    if deleted_rows == 0:
        # Возвращаем ошибку, если технический аккаунт не был удален
        return jsonify({'error': 'Технический аккаунт не найден'}), 404

    # Возвращаем сообщение об успешном удалении технического аккаунта
    return jsonify({'message': 'Технический аккаунт успешно удален'}), 200
