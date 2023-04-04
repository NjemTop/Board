from flask import Response
import logging
import peewee
import json
from DataBase.model_class import Release_info, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def api_data_release_versions():
        """Функция получения номеров версий отправки рассылки через API"""
        try:
            # Определяем список для хранения версий рассылок
            versions = []
            # Используем контекстный менеджер для выполнения операций с БД и автоматического закрытия соединения
            with conn:
                # Делаем выборку из таблицы Release_info по уникальным значениям даты и номера релиза
                for row in Release_info.select(Release_info.date, Release_info.release_number).distinct():
                    # Добавляем в список версий новую версию рассылки
                    versions.append({'Data': row.date, 'Number': row.release_number})
        except peewee.OperationalError as error_message:
            # Обработка исключения при возникновении ошибки подключения к БД
            web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
            print("Ошибка подключения к базе данных SQLite:", error_message)
            return "Ошибка с БД"
        # Формируем JSON с отступами для улучшения читабельности
        json_data = json.dumps(versions, ensure_ascii=False, indent=4)
        # Устанавливаем заголовок Access-Control-Allow-Origin
        response = Response(json_data, content_type='application/json; charset=utf-8')
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON
        return response

def api_data_release_number(version):
        """Функция просмотра контактов, кому ушла рассылка через API"""
        # Подключение к базе данных SQLite
        try:
            with conn:
                # Фильтрация данных по номеру релиза
                query = Release_info.select().where(Release_info.release_number == version)
                rows = list(query)
        except peewee.OperationalError as error_message:
            web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error_message)
            print("Ошибка подключения к базе данных SQLite:", error_message)
            return error_message
        # Создаём пустой массив
        data = []
        # Преобразование полученных данных в список словарей
        for row in rows:
            copy_addresses = []
            # Разбиваем строку со списком адресов электронной почты для копии на отдельные адреса
            if row.copy is None:
                copy_dict = [{'1': 'Копии отсутствуют'}]
            else:
                copy_addresses = row.copy.split(', ')
                # Формируем словарь для копий, который содержит адреса электронной почты с ключами 1, 2, 3 и т.д.
                copy_dict = [{f"{i+1}": copy_addresses[i]} for i in range(len(copy_addresses))]
            contacts = {
                'Main': row.main_contact,
                'Copy': copy_dict
            }
            # Добавляем данные в созданный ранее массив (создаём структуру данных JSON)
            data.append({
                'Data': row.date,
                'Number': row.release_number,
                'Client': row.client_name,
                'Contacts': contacts
            })
        # Форматирование JSON с отступами для улучшения читабельности
        json_data = json.dumps(data, ensure_ascii=False, indent=4)
        # Создание ответа с типом содержимого application/json и кодировкой UTF-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавление заголовка Access-Control-Allow-Origin для разрешения кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправка ответа JSON
        return response
