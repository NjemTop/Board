from flask import request, Response, jsonify
import logging
import json
import peewee
from werkzeug.utils import secure_filename
import os
from DataBase.model_class import ClientsCard, ConnectionInfo, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

UPLOAD_FOLDER = './connection_files'
ALLOWED_EXTENSIONS = {'docx'}

app = None

def init_app(flask_app):
    global app
    app = flask_app
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_uploaded_conn_files(client_id):
    try:
        client_card = ClientsCard.get(ClientsCard.client_id == client_id)
    except ClientsCard.DoesNotExist:
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def post_upload_conn_file(client_id):
    try:
        client_card = ClientsCard.get(ClientsCard.client_id == client_id)
    except ClientsCard.DoesNotExist:
        return {'error': f'Client with client_id {client_id} not found'}, 404

    if 'file' not in request.files:
        return {'error': 'No file part'}, 400

    file = request.files['file']
    text = request.form.get('text')

    if file.filename == '':
        return {'error': 'No selected file'}, 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Создание записи в БД
        connection_info = ConnectionInfo.create(client_id=client_card, file_path=os.path.join(app.config['UPLOAD_FOLDER'], filename), text=text)
        connection_info.save()
        return {'message': 'File uploaded and saved in the database successfully'}, 201
    else:
        return {'error': 'File format not allowed'}, 400
