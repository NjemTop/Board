from flask import request, Response, jsonify
import logging
import json
import peewee
import traceback
import datetime
from DataBase.model_class import BMInfo_onClient, ClientsCard, ContactsCard, СonnectInfoCard, Servise, TechInformation, TechAccount, BMServersCard, Integration, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def get_all_clients_api():
    """
    Функция GET-запроса, получения списка всех клиентов с его данными.
    Можно передать тело запроса в виде JSON: "client_name" : "Тестовый клиент",
    который выведит информацию об определённом клиенте
    """
    try:
        # Получаем параметр запроса client_name из JSON-данных в теле запроса, если заголовок Content-Type равен 'application/json'
        requested_client_name = None
        if request.content_type == 'application/json':
            json_data = request.json
            requested_client_name = json_data.get('client_name') if json_data else None

        # Соединение с базой данных
        with conn:
            if requested_client_name:
                # Фильтруем записи клиентов по имени, если задан параметр client_name
                client_infos = list(BMInfo_onClient.select().where(BMInfo_onClient.client_name == requested_client_name))
            else:
                client_infos = list(BMInfo_onClient.select())

        results = []
        # Итерация по всем клиентам
        for client_info in client_infos:
            result = {}
            # Итерация по столбцам таблицы BMInfo_onClient
            for column_name in client_info.column_names:
                result[column_name] = getattr(client_info, column_name)

            # Получаем связанные ClientsCard для текущего клиента
            clients_card = ClientsCard.select().where(ClientsCard.client_id == client_info.client_info).first()

            # Если запись clients_card не найдена, пропускаем итерацию
            if clients_card is None:
                continue

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
        # Записываем ошибку в лог файл
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        # Если возникла ошибка, формируем словарь с информацией об ошибке
        message = "Ошибка подключения к базе данных SQLite: {}".format(error_message)
        # Преобразуем словарь с информацией об ошибке в строку JSON
        json_data = json.dumps({"message": message}, ensure_ascii=False, indent=4)
        # Создаем ответ с заголовком Content-Type и кодировкой utf-8
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        # Добавляем заголовок Access-Control-Allow-Origin для поддержки кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON с информацией об ошибке
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
        required_fields = ['client_name', 'service_pack', 'manager', 'server_version']
        for field in required_fields:
            if field not in data:
                return f"Отсутствует обязательное поле: {field}", 400

        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([BMInfo_onClient, ClientsCard, ContactsCard, СonnectInfoCard, Servise, TechInformation])

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

                # Создаем запись в таблице Servise с полученным client_id и полями 'service_pack', 'manager' и 'loyal'
                Servise.create(
                    service_id=client_id,
                    service_pack=data['service_pack'],
                    manager=data['manager'],
                    loyal=data.get('loyal', None)
                )

                # Проверим, что полем 'server_version' указано и укажем сегодняшнюю дату в поле 'update_date'
                server_version = data['server_version']
                if not server_version.strip():
                    return {'error': "Поле 'server_version' должно быть непустой строкой"}, 400

                update_date = datetime.datetime.now().date()
                
                # Проверяем обязательные булевы поля и их значения
                boolean_fields = ['api', 'localizable_web', 'localizable_ios', 'skins_web', 'skins_ios']
                for field in boolean_fields:
                    if not isinstance(data[field], bool):
                        return f"Поле {field} должно быть булевым значением (True или False)", 400

                # Создаем словарь с необходимыми полями
                tech_information_fields = {key: data[key] for key in boolean_fields + ['ipad', 'android', 'mdm']}

                # Проверяем корректность типов данных для всех ключей
                for key, value in tech_information_fields.items():
                    if key not in boolean_fields and not isinstance(value, str):
                        return {'error': f"Поле '{key}' должно быть строкой"}, 400

                # Записываем всё в таблицу TechInformation с полученным технической информации
                TechInformation.create(
                    tech_information_id=new_client.technical_information,
                    server_version=server_version,
                    update_date=update_date,
                    **tech_information_fields
                )

                # Проверяем обязательные поля для массива с контактами
                contacts_data = data.get('contacts', [])
                for contact_data in contacts_data:
                    required_contact_fields = ['contact_name', 'contact_email']
                    for field in required_contact_fields:
                        if field not in contact_data:
                            return f"Отсутствует обязательное поле: {field}", 400
                    # Создаем записи в таблице ContactsCard для каждого контакта в списке контактов
                    new_contact = ContactsCard.create(
                        contact_id=new_client_card.contacts,
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

                # Проверяем обязательный поля для массива с технологической учётной записью
                for tech_account_data in data.get('tech_account', []):
                    tech_account_data_fields = ['contact_info_disc', 'contact_info_account', 'contact_info_password']
                    for field in tech_account_data_fields:
                        if field not in tech_account_data:
                            return f"Отсутствует обязательное поле: {field}", 400
                    # Создаем записи в таблице TechAccount для каждой учётной записи
                    TechAccount.create(
                        tech_account_id=new_client_card.tech_account,
                        contact_info_disc=tech_account_data['contact_info_disc'],
                        contact_info_account=tech_account_data['contact_info_account'],
                        contact_info_password=tech_account_data['contact_info_password']
                    )
                # Проверяем обязательный поля для массива с технологической учётной записью
                for bm_server_data in data.get('bm_servers_card', []):
                    bm_server_data_fields = ['bm_servers_circuit', 'bm_servers_servers_name', 'bm_servers_servers_adress', 'bm_servers_role']
                    for field in bm_server_data_fields:
                        if field not in bm_server_data:
                            return f"Отсутствует обязательное поле: {field}", 400
                        
                    # Создаем записи в таблице BMServersCard для каждой учётной записи
                    BMServersCard.create(
                        bm_servers_id=client_id,
                        bm_servers_circuit=bm_server_data['bm_servers_circuit'],
                        bm_servers_servers_name=bm_server_data['bm_servers_servers_name'],
                        bm_servers_servers_adress=bm_server_data['bm_servers_servers_adress'],
                        bm_servers_operation_system=bm_server_data.get('bm_servers_operation_system', None),
                        bm_servers_url=bm_server_data.get('bm_servers_url', None),
                        bm_servers_role=bm_server_data['bm_servers_role']
                    )
                
                # Получаем данные из массива integration об интеграции нового клиента
                integration = data.get('integration')

                # Добавляем проверку на булевые значения для полей в массиве integration
                integration_boolean_fields = [
                    'elasticsearch', 'ad', 'adfs', 'oauth_2', 'module_translate', 'ms_oos',
                    'exchange', 'office_365', 'sfb', 'zoom', 'teams', 'smtp', 'cryptopro_dss',
                    'cryptopro_scp', 'smpp', 'limesurvey'
                ]

                for field in integration_boolean_fields:
                    if not isinstance(integration[field], bool):
                        return f"Поле {field} должно быть булевым значением (True или False)", 400

                # Добавляем информацию об интеграции в БД
                Integration.create(
                    integration_id=new_client.integration,
                    **integration
                )

                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()

            else:
                return f"Клиент с именем {data['client_name']} уже существует.", 409

        web_info_logger.info("Добавлен клиент в БД: %s", data['client_name'])
        return f"Клиент {data['client_name']} успешно записаны в БД!", 201

    except peewee.OperationalError as error_message:
        # Обработка исключения при возникновении ошибки подключения к БД
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        return f"Ошибка с БД: {error_message}", 500
    except Exception as error:
        # Обработка остальных исключений
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}", 500
