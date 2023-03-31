from flask import request, Response
import logging
import json
import peewee
from DataBase.model_class import BMInfo_onClient, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)


def post_BM_Info_onClient_api():
    """Функция добавления о клиентах в БД"""
    try:
        # Получаем данные из запроса и создаем объект BMInfo_onClient
        data = json.loads(request.data.decode('utf-8'))
        # Создаем таблицу, если она не существует
        with conn:
            conn.create_tables([BMInfo_onClient])

        # Создаем транзакцию для сохранения данных в БД
        with conn.atomic():
            # Проверяем наличие существующего клиента с тем же именем
            existing_client = BMInfo_onClient.get_or_none(BMInfo_onClient.client_name == data['client_name'])
            if existing_client is None:
                client_name = data.get('client_name')
                if not client_name:
                    return 'Error: значение ключа "client_name" не указано!'

                contact_status = data.get('contact_status')
                if not contact_status:
                    return 'Error: значение ключа "contact_status" не указано!'

                notes = data.get('notes', None)
                # Создаем запись в БД с автоматически сгенерированным id
                new_client = BMInfo_onClient.create(
                    client_name=client_name,
                    contact_status=contact_status,
                    notes=notes
                )
                # Получаем id созданной записи
                client_id = new_client.id
                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                print(f"Клиент с именем {data['client_name']} уже существует. Пропускаем...")
                return f"Клиент с именем {data['client_name']} уже существует. Пропускаем..."

        web_info_logger.info("Добавлен клиент в БД: %s", data['client_name'])
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
