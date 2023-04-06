from flask import request, Response, send_from_directory
import logging
import json
import peewee
from werkzeug.utils import secure_filename
import re
from unicodedata import normalize
import os
from DataBase.model_class import ClientsCard, ConnectionInfo, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

# Выбираем путь куда будут сохраняться принимающие файлы
UPLOAD_FOLDER = './connection_files'
# Укажем формат каких файлов мы можем принимать
ALLOWED_EXTENSIONS = {'docx', 'pdf'}

app = None

def init_app(flask_app):
    global app
    app = flask_app
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def secure_filename_custom(filename):
    filename = normalize("NFKD", filename).encode("utf-8", "ignore").decode("utf-8")
    filename = re.sub(r"[^\w\s-]", "", filename).strip().lower()
    filename = re.sub(r"[-\s]+", "-", filename)
    return filename

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_uploaded_conn_files(client_id):
    try:
        client_card = ClientsCard.get(ClientsCard.client_id == client_id)
    except peewee.DoesNotExist:
        return {'error': f'Client with client_id {client_id} not found'}, 404

    connection_infos = ConnectionInfo.select().where(ConnectionInfo.client_id == client_card)

    if connection_infos.count() == 0:
        return {'error': f'No uploaded files found for client with client_id {client_id}'}, 404

    files = []

    for connection_info in connection_infos:
        file_data = {
            'id': connection_info.id,
            'file_path': connection_info.file_path,
            'text': connection_info.text
        }
        files.append(file_data)

    return {'client_id': client_id, 'files': files}, 200

def get_serve_file(client_id):
    try:
        client_card = ClientsCard.get(ClientsCard.client_id == client_id)
    except peewee.DoesNotExist:
        return {'error': f'Client with client_id {client_id} not found'}, 404

    connection_infos = ConnectionInfo.select().where(ConnectionInfo.client_id == client_card)

    if connection_infos.count() == 0:
        return {'error': f'No uploaded files found for client with client_id {client_id}'}, 404

    # Выбираем первый файл из списка (можно добавить логику выбора нужного файла, если требуется)
    connection_info = connection_infos[0]
    return send_from_directory(app.config['UPLOAD_FOLDER'], os.path.basename(connection_info.file_path))

def post_upload_conn_file(client_id):
    # Проверяем существование клиента с указанным client_id
    try:
        client_card = ClientsCard.get(ClientsCard.client_id == client_id)
    except peewee.DoesNotExist:
        return {'error': f'Client with client_id {client_id} not found'}, 404

    # Проверяем наличие файла в запросе
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400

    # Получаем файл и текст (если есть) из запроса
    file = request.files['file']
    text = request.form.get('text', None)

    # Проверяем наличие имени файла
    if file.filename == '':
        return {'error': 'No selected file'}, 400

    # Если файл существует и имеет допустимое расширение
    if file and allowed_file(file.filename):
        # Создаем безопасное имя файла и сохраняем его
        filename = secure_filename_custom(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Создание записи в БД
        connection_info = ConnectionInfo.create(client_id=client_card, file_path=os.path.join(app.config['UPLOAD_FOLDER'], filename), text=text)
        connection_info.save()

        # Возвращаем сообщение об успешной загрузке файла
        return {'message': 'File uploaded and saved in the database successfully'}, 201
    else:
        # Возвращаем ошибку, если формат файла не допустим
        return {'error': 'File format not allowed'}, 400
