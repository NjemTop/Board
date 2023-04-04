from flask import request, Response, jsonify
import logging
import json
import peewee
import traceback
from DataBase.model_class import СonnectInfoCard, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def get_connect_info_api():
    """Функция получения данных в БД со списком контактов клиентов"""
    try:
        # Используем контекстный менеджер для выполнения операций с БД
        with conn:
            # Получаем все записи из таблицы ConnectInfoCard
            connect_infos = list(СonnectInfoCard.select())
        
        # Создаем список для хранения результатов
        results = []
        for connect_info in connect_infos:
            # Создаем словарь для хранения данных одной записи контакта клиента
            result = {}
            for column_name in connect_info.column_names:
                # Используем названия столбцов для извлечения данных из объекта СonnectInfoCard
                result[column_name] = getattr(connect_info, column_name)
            # Добавляем словарь с данными контакта клиента в список результатов
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

def get_connect_info_by_id(id):
    """Функция возвращает информацию о подключении по указанному client_id."""
    try:
        with conn:
            # Получаем информацию о подключении по client_id
            connect_infos = СonnectInfoCard.select().where(СonnectInfoCard.client_id == id)

            if not connect_infos.exists():
                # Если информация о подключении с указанным ID не найдена, возвращаем сообщение об ошибке
                message = "Информация о подключении с ID {} не найдена".format(id)
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            # Здесь продолжайте с преобразованием данных и формированием ответа
            connect_infos_data = [
                {
                    'id': info.id,
                    'client_id': info.client_id,
                    'contact_info_name': info.contact_info_name,
                    'contact_info_account': info.contact_info_account,
                    'contact_info_password': info.contact_info_password
                } for info in connect_infos
            ]

            json_data = json.dumps(connect_infos_data, ensure_ascii=False, indent=4)
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

def post_connect_info_api():
    """Функция добавления информации о подключении в БД."""
    try:
        # Получаем данные из запроса
        data = json.loads(request.data.decode('utf-8'))

        # Проверяем обязательные поля
        if 'contact_info_name' not in data or 'contact_info_account' not in data or 'contact_info_password' not in data:
            return 'Ошибка: "contact_info_name", "contact_info_account" и "contact_info_password" являются обязательными полями.', 400

        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([СonnectInfoCard])

        # Создаем транзакцию для сохранения данных в БД
        with conn.atomic():
            # Проверяем наличие существующей записи с тем же contact_info_name, contact_info_account и client_id
            existing_info = СonnectInfoCard.get_or_none(
                (СonnectInfoCard.contact_info_name == data['contact_info_name']) &
                (СonnectInfoCard.contact_info_account == data['contact_info_account']) &
                (СonnectInfoCard.client_id == data['client_id'])
            )

            if existing_info is None:
                # Сохраняем данные в базе данных, используя insert и execute
                СonnectInfoCard.insert(**data).execute()
                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                # Обновляем существующую запись с данными из запроса
                СonnectInfoCard.update(**data).where(
                    (СonnectInfoCard.contact_info_name == data['contact_info_name']) &
                    (СonnectInfoCard.contact_info_account == data['contact_info_account']) &
                    (СonnectInfoCard.client_id == data['client_id'])
                ).execute()
                # Сохраняем изменения в БД
                conn.commit()

        web_info_logger.info("Добавлена/обновлена информация о подключении с ID: %s", data['client_id'])
        return 'Connect info data successfully saved to the database!', 201

    except peewee.OperationalError as error_message:
        # Обработка исключения при возникновении ошибки подключения к БД
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        return f"Ошибка с БД: {error_message}", 500
    except Exception as error:
        # Обработка остальных исключений
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}", 500

def delete_connect_info_api(id):
    """Функция удаления записи с информацией о подключении к клиенту по ID"""
    try:
        with conn:
            # Удаляем запись с указанным ID
            deleted_rows = СonnectInfoCard.delete().where(СonnectInfoCard.id == id).execute()

        if deleted_rows > 0:
            return f'Удалено {deleted_rows} записей с ID: {id}', 200
        else:
            return f'Запись с ID {id} не найдена', 404

    except peewee.OperationalError as error_message:
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        return jsonify({"message": f"Ошибка сервера: {error}", "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}), 500

def patch_connect_info_api(id):
    """Функция обновления информации о подключении к клиенту по ID"""
    data = request.get_json()

    # Получаем обновленные данные
    updated_data = {key: value for key, value in data.items() if key in СonnectInfoCard.COLUMN_NAMES and key != 'id'}

    if not updated_data:
        return 'Необходимо предоставить данные для обновления', 400

    try:
        with conn:
            # Обновляем запись с указанным ID
            updated_rows = СonnectInfoCard.update(updated_data).where(СonnectInfoCard.id == id).execute()

        if updated_rows > 0:
            return f'Обновлено {updated_rows} записей с ID: {id}', 200
        else:
            return f'Запись с ID {id} не найдена', 404

    except peewee.OperationalError as error_message:
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        return jsonify({"message": f"Ошибка сервера: {error}", "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}), 500
