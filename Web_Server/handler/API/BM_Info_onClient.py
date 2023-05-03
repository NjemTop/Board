from flask import request, Response, jsonify
import logging
import json
import peewee
import traceback
from DataBase.model_class import BMInfo_onClient, ClientsCard, Servise, TechInformation, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def get_BM_Info_onClient_api():
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

            # Получаем информацию об услугах и технической информации для текущего клиента
            service_info = Servise.get_or_none(Servise.service_id == client_info)
            tech_info = TechInformation.get_or_none(TechInformation.tech_information_id == client_info.technical_information)

            # Добавляем необходимые поля из таблиц Servise и TechInformation в словарь с данными клиента
            important_info = {}
            if service_info and service_info.service_pack:
                important_info['service_pack'] = service_info.service_pack
            if service_info and service_info.manager:
                important_info['manager'] = service_info.manager
            if tech_info and tech_info.server_version:
                important_info['server_version'] = tech_info.server_version
            if tech_info and tech_info.update_date:
                important_info['update_date'] = tech_info.update_date
            result['important_info'] = important_info
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

def post_BM_Info_onClient_api():
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

def patch_BM_Info_onClient_api():
    """Функция обновления данных в БД (обязательный ключ - client_name)"""
    data = request.get_json()

    # Получаем имя клиента, которое нужно обновить
    client_name = data.get('client_name', None)

    if not client_name:
        return 'Необходимо указать имя клиента для обновления', 400

    # Получаем обновленные данные
    updated_data = {key: value for key, value in data.items() if key != 'client_name'}

    if not updated_data:
        return 'Необходимо предоставить данные для обновления', 400

    try:
        with conn:
            # Обновляем запись с указанным именем клиента
            updated_rows = (BMInfo_onClient.update(updated_data).where(BMInfo_onClient.client_name == client_name).execute())

        if updated_rows > 0:
            return f'Обновлено {updated_rows} записей с именем клиента: {client_name}', 200
        else:
            return f'Клиент с именем {client_name} не найден', 404

    except peewee.OperationalError as error_message:
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        return jsonify({"message": f"Ошибка сервера: {error}", "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}), 500

def delete_BM_Info_onClient_api():
    """Функция удаления клиента из БД (ключ для приёма - client_name)"""
    # Получение данных из запроса в формате JSON
    data = request.get_json()
    # Извлечение имени клиента из данных запроса, значение по умолчанию - None
    client_name = data.get('client_name', None)

    # Проверка наличия имени клиента в запросе
    if not client_name:
        return 'Необходимо указать имя клиента для удаления', 400

    try:
        # Открываем соединение с базой данных
        with conn:
            # Удаление записи с указанным именем клиента
            deleted_rows = BMInfo_onClient.delete().where(BMInfo_onClient.client_name == client_name).execute()
        # Если удалена хотя бы одна запись, возвращаем количество удаленных записей и успешный статус
        if deleted_rows > 0:
            return f'Удалено {deleted_rows} записей с именем клиента: {client_name}', 200
        else:
            # Если запись с указанным именем клиента не найдена, возвращаем ошибку 404
            return f'Клиент с именем {client_name} не найден', 404

    except peewee.OperationalError as error_message:
        # Обработка ошибки подключения к базе данных SQLite
        return f"Ошибка подключения к базе данных SQLite: {error_message}", 500
    except Exception as error:
        # Обработка остальных ошибок сервера
        return f"Ошибка сервера: {error}", 500
