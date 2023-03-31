from flask import request, Response
import logging
import json
import peewee
import traceback
from DataBase.model_class import ClientsCard, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

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
            existing_client = ClientsCard.get_or_none(ClientsCard.clients_id == data['clients_id'])
            if existing_client is None:
                # Сохраняем данные в базе данных, используя insert и execute
                ClientsCard.insert(**data).execute()
                # Добавляем вызов commit() для сохранения изменений в БД
                conn.commit()
            else:
                print(f"Клиент с ID {data['clients_id']} уже существует. Пропускаем...")
                return f"Клиент с ID {data['clients_id']} уже существует. Пропускаем..."

        web_info_logger.info("Добавлен клиент в БД: %s", data['clients_id'])
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
