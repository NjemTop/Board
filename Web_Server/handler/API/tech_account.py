from flask import request, Response, jsonify
import logging
import json
import peewee
import traceback
from DataBase.model_class import ClientsCard, TechAccount, BMInfo_onClient, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def get_all_tech_accounts():
    clients_data = []

    try:
        with conn:
            # Получаем всех активных клиентов
            clients = BMInfo_onClient.select().where(BMInfo_onClient.contact_status == True)

        for client in clients:
            # Формируем информацию о клиенте
            client_data = {
                "client_id": client.client_info,
                "client_name": client.client_name,
                "tech_accounts": []
            }

            # Получаем технические аккаунты для текущего клиента
            tech_account_id = client.technical_information

            with conn:
                tech_accounts = TechAccount.select().where(TechAccount.tech_account_id == tech_account_id)

            for tech_account in tech_accounts:
                # Формируем информацию о техническом аккаунте
                account_data = {column_name: getattr(tech_account, column_name) for column_name in TechAccount.COLUMN_NAMES if column_name != 'tech_account_id'}
                client_data["tech_accounts"].append(account_data)

            clients_data.append(client_data)

    except peewee.DoesNotExist as e:
        return jsonify({'error': 'Нет данных о клиентах или технических аккаунтах', 'details': str(e)}, ensure_ascii=False), 404
    except peewee.OperationalError as e:
        return jsonify({'error': 'Ошибка подключения к базе данных', 'details': str(e)}, ensure_ascii=False), 500
    except Exception as e:
        return jsonify({'error': f'Ошибка сервера: {e}', 'details': str(e)}, ensure_ascii=False), 500

    # Возвращаем результат в виде JSON-объекта
    response = Response(json.dumps(clients_data, indent=2, ensure_ascii=False), content_type='application/json; charset=utf-8')
    response.headers.add('Cache-Control', 'no-store')
    response.headers.add('Pragma', 'no-cache')
    return response, 200

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
    """Функция удаления записи с техническим аккаунтом по ID"""
    try:
        with conn:
            # Удаляем запись с указанным ID
            deleted_rows = TechAccount.delete().where(TechAccount.id == id).execute()

    except peewee.OperationalError as error_message:
        # Возвращаем ошибку, если возникла проблема с подключением к базе данных
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        # Возвращаем ошибку, если возникла другая ошибка сервера
        return jsonify({"message": f"Ошибка сервера: {error}", "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}), 500

    # Проверяем, была ли удалена запись
    if deleted_rows > 0:
        # Возвращаем сообщение об успешном удалении записи
        return f'Удалено {deleted_rows} записей с ID: {id}', 200
    else:
        # Возвращаем ошибку, если запись с указанным ID не найдена
        return f'Запись с ID {id} не найдена', 404
