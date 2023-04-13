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
        # Соединение с базой данных
        with conn:
            client_infos = list(BMInfo_onClient.select())

        results = []
        # Итерация по всем клиентам
        for client_info in client_infos:
            result = {}
            # Итерация по столбцам таблицы BMInfo_onClient
            for column_name in client_info.column_names:
                result[column_name] = getattr(client_info, column_name)

            # Получаем связанные ClientsCard для текущего клиента
            clients_card = ClientsCard.get(ClientsCard.client_id == client_info.client_info)
            # Получаем поле 'contacts' из связанной таблицы ClientsCard
            contacts_id = clients_card.contacts

            # Получаем связанные контакты для текущего клиента
            contacts = ContactsCard.select().where(ContactsCard.contact_id == contacts_id)
            contacts_data = []
            # Итерация по контактам
            for contact in contacts:
                contact_dict = {}
                # Итерация по столбцам таблицы ContactsCard
                for column_name in contact.column_names:
                    contact_dict[column_name] = getattr(contact, column_name)
                contacts_data.append(contact_dict)

            # Добавляем список контактов к данным клиента
            result["contacts"] = contacts_data

            # Получаем связанные записи из таблицы СonnectInfoCard
            connect_info_cards = СonnectInfoCard.select().where(СonnectInfoCard.client_id == client_info.client_info)
            connect_info_cards_data = []
            # Итерация по connect_info_cards
            for card in connect_info_cards:
                card_dict = {}
                # Итерация по столбцам таблицы СonnectInfoCard
                for column_name in card.column_names:
                    card_dict[column_name] = getattr(card, column_name)
                connect_info_cards_data.append(card_dict)

            # Добавляем список connect_info_cards к данным клиента
            result["connect_info_cards"] = connect_info_cards_data
            results.append(result)

        # Преобразуем результат в JSON и возвращаем его
        json_data = json.dumps(results, ensure_ascii=False, indent=4)
        # Создаем ответ с заголовком Content-Type и кодировкой utf-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавляем заголовок Access-Control-Allow-Origin для поддержки кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON
        return response, 200
    except peewee.OperationalError as error_message:
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        print("Ошибка подключения к базе данных SQLite:", error_message)
        message = "Ошибка подключения к базе данных SQLite: {}".format(error_message)
        json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
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
        return response, 500
    
def post_all_clients_api():
    """
    Функция добавления информации о клиентах в БД через API.
    Обрабатывает HTTP POST-запросы и сохраняет информацию о клиентах
    в базе данных.
    """
    try:
        # Получаем данные из запроса и создаем объект BMInfo_onClient
        data = json.loads(request.data.decode('utf-8'))

        # Проверяем обязательный ключи
        required_fields = ['client_name']
        for field in required_fields:
            if field not in data:
                return f"Отсутствует обязательное поле: {field}", 400
            
        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([BMInfo_onClient, ClientsCard, ContactsCard, СonnectInfoCard])

        # Создаем транзакцию для сохранения данных в БД
        with conn.atomic():
            # Проверяем наличие существующего клиента с тем же именем
            existing_client = BMInfo_onClient.get_or_none(BMInfo_onClient.client_name == data['client_name'])
            if existing_client is None:
                # Создаем запись в таблице BMInfo_onClient
                new_client = BMInfo_onClient.create(
                    client_name=data['client_name'],
                    contact_status=True,
                    notes=data.get('notes')
                )
                # Получаем id созданной записи
                client_id = new_client.client_info

                # Создаем запись в таблице ClientsCard с полученным client_id
                new_client_card = ClientsCard.create(client_id=client_id)

                # Проверяем обязательные поля для массива с контактами
                contacts_data = data.get('contacts', [])
                for contact_data in contacts_data:
                    required_contact_fields = ['contact_name', 'contact_email']
                    for field in required_contact_fields:
                        if field not in contact_data:
                            return f"Отсутствует обязательное поле: {field}", 400
                    # Создаем записи в таблице ContactsCard для каждого контакта в списке контактов
                    new_contact = ContactsCard.create(
                        contact_id=client_id,
                        contact_name=contact_data['contact_name'],
                        contact_position=contact_data.get('contact_position'),
                        contact_email=contact_data['contact_email'],
                        notification_update=contact_data.get('notification_update'),
                        contact_notes=contact_data.get('contact_notes')
                    )

                # Проверяем обязательный поля для массива с учётными записями для ВПН
                for connect_info_data in data.get('connect_info_cards', []):
                    required_connect_info_fields = ['contact_info_name', 'contact_info_account', 'contact_info_password']
                    for field in required_connect_info_fields:
                        if field not in connect_info_data:
                            return f"Отсутствует обязательное поле: {field}", 400  
                    # Создаем записи в таблице СonnectInfoCard для каждой учётной записи
                    СonnectInfoCard.create(
                        client_id=client_id,
                        contact_info_name=connect_info_data['contact_info_name'],
                        contact_info_account=connect_info_data['contact_info_account'],
                        contact_info_password=connect_info_data['contact_info_password'],
                    )

                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                return f"Клиент с именем {data['client_name']} уже существует.", 409

        web_info_logger.info("Добавлен клиент в БД: %s", data['client_name'])
        return 'Клиент успешно записаны в БД!', 201

    except peewee.OperationalError as error_message:
        # Обработка исключения при возникновении ошибки подключения к БД
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        return f"Ошибка с БД: {error_message}", 500
    except Exception as error:
        # Обработка остальных исключений
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}", 500