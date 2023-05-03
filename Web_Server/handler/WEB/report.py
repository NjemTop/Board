from flask import request, Response, render_template
import logging
import peewee
import json
import datetime
from DataBase.model_class import Report_Ticket, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def report_tickets():
    try:
        output_data = ['Консультация', 'Консультация', 'Доработка', 'Проблема в инфраструктуре', 'Шаблоны']
        return render_template('index.html', data=output_data)

    except peewee.OperationalError as error:
        # Обработка ошибок, связанных с базой данных
        error_message = f"Database error: {error}"
        return render_template('error.html', error_message=error_message)

    except Exception as error:
        # Обработка всех остальных ошибок
        error_message = f"An unexpected error occurred: {error}"
        return render_template('error.html', error_message=error_message)

def get_report_tickets():
    try:
        with conn:
            conn.create_tables([Report_Ticket])
            # Получаем все записи из таблицы report_ticket
            query = Report_Ticket.select()
            results = [entry.__data__ for entry in query]

        # Преобразуем список результатов в строку JSON
        json_data = json.dumps(results, ensure_ascii=False, indent=4, default=str)
        # Создаем ответ с заголовком Content-Type и кодировкой utf-8
        response = Response(json_data, content_type='application/json; charset=utf-8')
        # Добавляем заголовок Access-Control-Allow-Origin для поддержки кросс-доменных запросов
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Отправляем ответ JSON
        return response

    except peewee.OperationalError as error:
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error)
        return f"Ошибка с БД: {error}", 500

    except Exception as error:
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}", 500
    
def post_report_tickets():
    try:
        # Получаем и декодируем данные запроса в формате JSON
        input_data = json.loads(request.data.decode('utf-8'))

        # Получаем строки с датами из входных данных
        report_date_str = input_data['report_date']
        creation_date_str = input_data['creation_date']
        updated_at_str = input_data['updated_at']
        last_reply_at_str = input_data['last_reply_at']

        # Преобразование строк с датами в объекты datetime.date
        for key in ['report_date', 'creation_date', 'updated_at', 'last_reply_at']:
            try:
                input_data[key] = datetime.datetime.strptime(input_data[key], "%d-%m-%Y").date()
            except ValueError:
                return {'error': f"Поле '{key}' должно быть корректной датой в формате 'DD-MM-YYYY'"}, 400

        # Преобразование строк с продолжительностью времени в минуты
        for key in ['sla_time', 'response_time']:
            hours, minutes = map(int, input_data[key].split(' ')[::2])
            input_data[key] = hours * 60 + minutes

        # Создание таблицы, если она не существует
        with conn:
            conn.create_tables([Report_Ticket])

            # Создание и сохранение нового объекта Report_Ticket
            new_ticket = Report_Ticket.create(**input_data)

        web_info_logger.info("Добавлен новый отчёт о тикете с ID: %s", new_ticket.id)
        return 'Отчёт о тиете был успешно сохранён в БД', 201

    except peewee.IntegrityError as error:
        web_error_logger.error("Ошибка целостности данных: %s", error)
        return f"Ошибка: нарушены ограничения целостности данных.", 409

    except peewee.OperationalError as error:
        web_error_logger.error("Ошибка подключения к базе данных SQLite: %s", error)
        return f"Ошибка с БД: {error}", 500

    except Exception as error:
        web_error_logger.error("Ошибка сервера: %s", error)
        return f"Ошибка сервера: {error}", 500
