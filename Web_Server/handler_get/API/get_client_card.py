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
                json_data = json.dumps({"message": message}, ensure_ascii=False)
                response = Response(json_data, content_type='application/json; charset=utf-8', status=404)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            # Здесь продолжайте с преобразованием данных и формированием ответа
            client_data = {
                'client_id': client.client_id,
                'contacts': client.contacts,
                'tech_notes': client.tech_notes,
                'connect_info': client.connect_info,
                'rdp': client.rdp,
                'tech_account': client.tech_account,
                'bm_servers': client.bm_servers
            }

            json_data = json.dumps(client_data, ensure_ascii=False)
            response = Response(json_data, content_type='application/json; charset=utf-8')
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

    except peewee.OperationalError as error_message:
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
        print("Ошибка подключения к базе данных SQLite:", error_message)
        message = "Ошибка подключения к базе данных SQLite: {}".format(error_message)
        json_data = json.dumps({"message": message}, ensure_ascii=False)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as error:
        web_error_logger.error("Ошибка сервера: %s", error)
        print("Ошибка сервера:", error)
        message = "Ошибка сервера: {}".format(error)
        json_data = json.dumps({"message": message, "error_type": str(type(error).__name__), "error_traceback": traceback.format_exc()}, ensure_ascii=False)
        response = Response(json_data, content_type='application/json; charset=utf-8', status=500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
