from flask import request, Response, jsonify
import logging
import json
import peewee
import traceback
from DataBase.model_class import ClientsCard, BMInfo_onClient, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def get_client_card_api():
    """Функция получения данных в БД со списком карточек клиентов"""
    try:
        # Используем контекстный менеджер для выполнения операций с БД
        with conn:
            # Получаем все записи из таблицы ClientsCard
            client_cards = list(ClientsCard.select())
        
        # Создаем список для хранения результатов
        results = []
        for client_card in client_cards:
            # Создаем словарь для хранения данных одной карточки клиента
            result = {}
            for column_name in client_card.column_names:
                # Используем названия столбцов для извлечения данных из объекта ClientsCard
                result[column_name] = getattr(client_card, column_name)
            # Добавляем словарь с данными карточки клиента в список результатов
            results.append(result)
        
        # Преобразуем список результатов в строку JSON
        json_data = json.dumps(results, ensure_ascii=False, indent=4)
        # Создаем ответ с заголовком Content-Type и кодировкой utf-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавляем заголовок Access-Control-Allow-Origin для поддержки кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON
        return response

    except Exception as error:
        # Если возникла ошибка, формируем словарь с информацией об ошибке
        error_message = {"error": str(error)}
        # Преобразуем словарь с информацией об ошибке в строку JSON
        json_data = json.dumps(error_message, ensure_ascii=False, indent=4)
        # Создаем ответ с заголовком Content-Type и кодировкой utf-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавляем заголовок Access-Control-Allow-Origin для поддержки кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON с информацией об ошибке
        return response

def get_client_by_id(id):
    """Функция возвращает данные клиента по указанному id (client_id)."""
    try:
        with conn:
            # Получаем данные клиента по id
            client = ClientsCard.get_or_none(ClientsCard.client_id == id)

            if client is None:
                # Если клиент с указанным ID не найден, возвращаем сообщение об ошибке
                message = "Клиент с ID {} не найден".format(id)
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            bm_client = BMInfo_onClient.get_or_none(BMInfo_onClient.client_info == id)

            if bm_client is None:
                message = "Информация о клиенте с ID {} не найдена в таблице BM_info_on_clients".format(id)
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            # Преобразованием данных и формируем ответ
            client_data = {
                'client_id': client.client_id,
                'client_name': bm_client.client_name,
                'contact_status': bm_client.contact_status
            }

            json_data = json.dumps(client_data, ensure_ascii=False, indent=4)
            response = Response(json_data, content_type='application/json; charset=utf-8')
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

    except peewee.OperationalError as error_message:
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        print("Ошибка подключения к базе данных SQLite:", error_message)
        message = "Ошибка подключения к базе данных SQLite: {}".format(error_message)
        json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as error:
        web_error_logger.error("Ошибка сервера: %s", error)
        print("Ошибка сервера:", error)
        message = "Ошибка сервера: {}".format(error)
        json_data = json.dumps({"message": message, "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

def post_client_card_api():
    """Функция добавления данных карточек клиентов в БД"""
    try:
        # Получаем данные из запроса и создаем объект ClientsCard
        data = json.loads(request.data.decode('utf-8'))
        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([ClientsCard])

        # Создаем транзакцию для сохранения данных в БД
        with conn.atomic():
            # Проверяем наличие существующего клиента с тем же ID
            existing_client = ClientsCard.get_or_none(ClientsCard.client_id == data['client_id'])
            if existing_client is None:
                # Сохраняем данные в базе данных, используя insert и execute
                ClientsCard.insert(**data).execute()
                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                print(f"Контакт с ID {data['client_id']} уже существует. Пропускаем...")
                return f"Контакт с ID {data['client_id']} уже существует. Пропускаем...", 409

        web_info_logger.info("Добавлен контакт в БД: %s", data['client_id'])
        return 'Контакт успешно записаны в БД!', 201

    except peewee.OperationalError as error_message:
        # Обработка исключения при возникновении ошибки подключения к БД
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        web_error_logger.error("Ошибка подключения к базе данных SQLite:%s", error_message)
        return f"Ошибка с БД: {error_message}"
    except Exception as error:
        # Обработка остальных исключений
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}"

def post_client_card_api_by_id(id):
    """Функция добавления данных карточек клиентов в БД с указанным id клиента"""
    try:
        # Получаем данные из запроса и создаем объект ClientsCard
        data = json.loads(request.data.decode('utf-8'))
        # Добавляем переданный id клиента в данные
        data['client_id'] = id
        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([ClientsCard])

        # Создаем транзакцию для сохранения данных в БД
        with conn.atomic():
            # Проверяем наличие существующего клиента с тем же ID
            existing_client = ClientsCard.get_or_none(ClientsCard.client_id == id)
            if existing_client is None:
                # Сохраняем данные в базе данных, используя insert и execute
                ClientsCard.insert(**data).execute()
                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                print(f"Карточка клиента с ID {id} уже существует. Пропускаем...")
                return f"Карточка клиента с ID {id} уже существует. Пропускаем..."

        web_info_logger.info("Добавлена карточка клиента с ID: %s", id)
        return 'Data successfully saved to the database!'

    except peewee.OperationalError as error_message:
        # Обработка исключения при возникновении ошибки подключения к БД
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        web_error_logger.error("Ошибка подключения к базе данных SQLite:%s", error_message)
        return f"Ошибка с БД: {error_message}"
    except Exception as error:
        # Обработка остальных исключений
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}"

def patch_client_card_api(id):
    """Функция изменений данных в БД со списком карточек клиентов"""
    data = request.get_json()

    # Получаем обновленные данные
    updated_data = {key: value for key, value in data.items() if key != 'client_id'}

    if not updated_data:
        return 'Необходимо предоставить данные для обновления', 400

    try:
        with conn:
            # Обновляем запись с указанным ID клиента
            updated_rows = (BMInfo_onClient.update(updated_data).where(BMInfo_onClient.client_info == id).execute())

        if updated_rows > 0:
            return f'Обновлено {updated_rows} записей с ID клиента: {id}', 200
        else:
            return f'Клиент с ID {id} не найден', 404

    except peewee.OperationalError as error_message:
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        return jsonify({"message": f"Ошибка сервера: {error}", "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}), 500

def delete_client_card_api():
    """Функция удаления данных в БД со списком карточек клиентов"""
    # Получение данных из запроса в формате JSON
    data = request.get_json()
    # Извлечение ID клиента из данных запроса, значение по умолчанию - None
    clients_id = data.get('clients_id', None)

    # Проверка наличия ID клиента в запросе
    if not clients_id:
        return 'Необходимо указать ID клиента для удаления', 400

    try:
        # Открываем соединение с базой данных
        with conn:
            # Удаление записи с указанным ID клиента
            deleted_rows = ClientsCard.delete().where(ClientsCard.clients_id == clients_id).execute()
        # Если удалена хотя бы одна запись, возвращаем количество удаленных записей и успешный статус
        if deleted_rows > 0:
            return f'Удалено {deleted_rows} записей с ID клиента: {clients_id}', 200
        else:
            # Если запись с указанным ID клиента не найдена, возвращаем ошибку 404
            return f'Клиент с ID {clients_id} не найден', 404

    except peewee.OperationalError as error_message:
        # Обработка ошибки подключения к базе данных SQLite
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        # Обработка остальных ошибок сервера
        return f"Ошибка сервера: {error}", 500
