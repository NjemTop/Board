from flask import request, Response, render_template
import logging
import peewee
from DataBase.model_class import Release_info, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def data_release_html():
    try:
        release_number = request.args.get('release_number', 'all')

        if release_number == 'all':
            query = Release_info.select()
        else:
            query = Release_info.select().where(Release_info.release_number == release_number)

        data = []
        for row in query:
            data.append({
                'Дата_рассылки': row.date,
                'Номер_релиза': row.release_number,
                'Наименование_клиента': row.client_name,
                'Основной_контакт': row.main_contact,
                'Копия': row.copy
            })
        return render_template('data_release.html', data=data)

    except peewee.OperationalError as error:
        # Обработка ошибок, связанных с базой данных
        error_message = f"Database error: {error}"
        return render_template('error.html', error_message=error_message)

    except Exception as error:
        # Обработка всех остальных ошибок
        error_message = f"An unexpected error occurred: {error}"
        return render_template('error.html', error_message=error_message)
