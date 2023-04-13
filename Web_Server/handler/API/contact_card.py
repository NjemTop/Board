from flask import request, Response, jsonify
import logging
import json
import peewee
import traceback
from DataBase.model_class import BMInfo_onClient, ClientsCard, ContactsCard, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def get_contact_by_client_id(id):
    """Функция возвращает информацию о контактах для клиента с указанным client_id."""
    try:
        with conn:
            # Получаем контакты клиента по client_id
            client = ClientsCard.get_or_none(ClientsCard.client_id == id)

            if client is None:
                message = "Клиент с ID {} не найден".format(id)
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            
            contacts = ContactsCard.select().where(ContactsCard.contact_id == client)

            if not contacts.exists():
                message = "Контакты для клиента с ID {} не найдены".format(id)
                json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            client_name = BMInfo_onClient.get(BMInfo_onClient.client_info == id).client_name

            contacts_data = []
            for contact in contacts:
                contacts_data.append({
                    'contact_name': contact.contact_name,
                    'contact_email': contact.contact_email,
                    'contact_position': contact.contact_position,
                    'notification_update': contact.notification_update,
                    'contact_notes': contact.contact_notes
                })

            result = {
                'client': client_name,
                'client_id': id,
                'contacts': contacts_data
            }

            json_data = json.dumps(result, ensure_ascii=False, indent=4)
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

def post_contact_api_by_id(id):
    """Функция добавления контактов в БД с указанным id клиента."""
    try:
        # Получаем данные из запроса
        data = json.loads(request.data.decode('utf-8'))
        
        # Проверяем обязательные поля
        if 'contact_name' not in data or 'contact_email' not in data:
            return 'Ошибка: "contact_name" и "contact_email" являются обязательными полями.', 400

        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([ContactsCard, ClientsCard])

        # Получаем значение contacts для указанного client_id из таблицы ClientsCard
        client = ClientsCard.get_or_none(ClientsCard.client_id == id)
        if client is None:
            return f"Ошибка: клиент с ID {id} не найден.", 404

        # Создаем транзакцию для сохранения данных в БД
        with conn.atomic():
            # Проверяем наличие существующего контакта с тем же email
            existing_contact = ContactsCard.get_or_none(ContactsCard.contact_email == data['contact_email'])

            if existing_contact is None:
                # Сохраняем данные в базе данных, используя insert и execute
                ContactsCard.insert(**data).execute()
                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                return f"Контакт с email {data['contact_email']} уже существует. Пропускаем...", 409

        web_info_logger.info("Добавлен контакт для клиента с ID: %s", id)
        return 'Contact data successfully saved to the database!', 201
    
    except peewee.IntegrityError as error:
        # Обработка исключения при нарушении ограничений целостности
        web_error_logger.error("Ошибка целостности данных: %s", error)
        return f"Ошибка: указанный Email {data['contact_email']} уже есть в БД.", 409
    
    except peewee.OperationalError as error_message:
        # Обработка исключения при возникновении ошибки подключения к БД
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        web_error_logger.error("Ошибка подключения к базе данных SQLite:%s", error_message)
        return f"Ошибка с БД: {error_message}", 500
    
    except Exception as error:
        # Обработка остальных исключений
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}", 500
