from flask import request, Response, render_template
import logging
import sqlite3
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

# Путь к БД (старый, прямой формат)
db_filename = '/var/lib/sqlite/database.db'

def data_release_html():
        release_number = request.args.get('release_number', 'all')
        onn = sqlite3.connect(f'file:{db_filename}')
        cur = onn.cursor()
        if release_number == 'all':
            cur.execute('SELECT * FROM info')
        else:
            cur.execute('SELECT * FROM info WHERE "Номер_релиза" = ?', (release_number,))
        rows = cur.fetchall()
        onn.close()
        data = []
        for row in rows:
            data.append({
                'Дата_рассылки': row[0],
                'Номер_релиза': row[1],
                'Наименование_клиента': row[2],
                'Основной_контакт': row[3],
                'Копия': row[4]
            })
        return render_template('data_release.html', data=data)
