from flask import request, Response, jsonify
import logging
import json
import peewee
import traceback
from DataBase.model_class import BMInfo_onClient, ClientsCard, ContactsCard, СonnectInfoCard, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def get_all_clients_api():
    try:
        with conn:
            client_infos = list(BMInfo_onClient.select())

        results = []

        for client_info in client_infos:
            client_data = {}
            for column_name in client_info.column_names:
                client_data[column_name] = getattr(client_info, column_name)

            client_id = client_data['client_info']

            contacts = list(ContactsCard.select().where(ContactsCard.contact_id == client_id))
            contact_list = []
            for contact in contacts:
                contact_data = {}
                for column_name in contact.column_names:
                    contact_data[column_name] = getattr(contact, column_name)
                contact_list.append(contact_data)

            connect_info_cards = list(СonnectInfoCard.select().where(СonnectInfoCard.client_id == client_id))
            connect_info_list = []
            for connect_info_card in connect_info_cards:
                connect_info_data = {}
                for column_name in connect_info_card.column_names:
                    connect_info_data[column_name] = getattr(connect_info_card, column_name)
                connect_info_list.append(connect_info_data)

            client_data['contacts'] = contact_list
            client_data['connect_info_cards'] = connect_info_list

            results.append(client_data)

        json_data = json.dumps(results, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8')
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as error:
        error_message = {"error": str(error)}
        json_data = json.dumps(error_message, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8')
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

# def get_all_clients_api():
    try:
        # Используем контекстный менеджер для выполнения операций с БД
        with conn:
            # Получаем все записи из таблицы client_info
            client_infos = list(BMInfo_onClient.select())
        # Создаем список для хранения результатов
        results = []
        for client_info in client_infos:
            # Создаем словарь для хранения данных одного клиента
            result = {}
            for column_name in client_info.column_names:
                # Используем названия столбцов для извлечения данных из объекта BMInfo_onClient
                result[column_name] = getattr(client_info, column_name)
            # Добавляем словарь с данными клиента в список результатов
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
    
def post_all_clients_api():
    """
    Функция добавления информации о клиентах в БД через API.
    Обрабатывает HTTP POST-запросы и сохраняет информацию о клиентах
    в базе данных.
    """
    try:
        # Получаем данные из запроса и создаем объект BMInfo_onClient
        data = json.loads(request.data.decode('utf-8'))
        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([BMInfo_onClient, ClientsCard])

        # Создаем транзакцию для сохранения данных в БД
        with conn.atomic():
            # Проверяем наличие существующего клиента с тем же именем
            existing_client = BMInfo_onClient.get_or_none(BMInfo_onClient.client_name == data['client_name'])
            if existing_client is None:
                # Создаем запись в таблице BMInfo_onClient
                new_client = BMInfo_onClient.create(
                    client_name=data['client_name'],
                    contact_status=data['contact_status'],
                    notes=data.get('notes')
                )
                # Получаем id созданной записи
                client_id = new_client.id

                # Создаем запись в таблице ClientsCard с полученным client_id
                new_client_card = ClientsCard.create(client_id=client_id)

                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                print(f"Клиент с именем {data['client_name']} уже существует. Пропускаем...")
                return f"Клиент с именем {data['client_name']} уже существует. Пропускаем...", 409

        web_info_logger.info("Добавлен клиент в БД: %s", data['client_name'])
        return 'Клиент успешно записаны в БД!', 201

    except peewee.OperationalError as error_message:
        # Обработка исключения при возникновении ошибки подключения к БД
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        web_error_logger.error("Ошибка подключения к базе данных SQLite:%s", error_message)
        return f"Ошибка с БД: {error_message}", 500
    except Exception as error:
        # Обработка остальных исключений
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}", 500