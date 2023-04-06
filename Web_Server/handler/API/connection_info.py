from flask import request, Response, jsonify, send_file, make_response
import mimetypes
import logging
import time
import peewee
from werkzeug.utils import secure_filename
import re
from unicodedata import normalize
import os
import base64
from DataBase.model_class import ClientsCard, ConnectionInfo, conn
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

# Выбираем путь куда будут сохраняться принимающие файлы
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
UPLOAD_FOLDER = os.path.join(PROJECT_DIR, 'connection_files')

# Укажем формат каких файлов мы можем принимать
ALLOWED_EXTENSIONS = {'docx', 'pdf'}

app = None

def init_app(flask_app):
    global app
    app = flask_app
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def unique_filename(filename):
    timestamp = int(time.time())
    return f"{timestamp}_{filename}"

def secure_filename_custom(filename):
    basename, ext = os.path.splitext(filename)
    basename = normalize("NFKD", basename).encode("utf-8", "ignore").decode("utf-8")
    basename = re.sub(r"[^\w\s-]", "", basename).strip().lower()
    basename = re.sub(r"[-\s]+", "-", basename)
    return f"{basename}{ext}"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_uploaded_conn_files(client_id):
    """Функция определения списка файлов у клиента по запросу client_id"""
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
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(connection_info.file_path))

    # Определение MIME-типа файла
    mimetype = mimetypes.guess_type(file_path)[0]

    # Отправка файла с правильным MIME-типом
    response = make_response(send_file(file_path, mimetype=mimetype))

    # Добавление заголовков, чтобы предотвратить кеширование
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response

def post_upload_conn_file(client_id):
    # Проверяем существование клиента с указанным client_id
    try:
        client_card = ClientsCard.get(ClientsCard.client_id == client_id)
    except peewee.DoesNotExist:
        return {'error': f'Client with client_id {client_id} not found'}, 404

    # Проверяем наличие файла в запросе
    if 'file' not in request.files:
        return {'error': 'No file part'}, 400

    # Получаем файл, текст (если есть) и формат файла из запроса
    file = request.files['file']
    text = request.form.get('text', None)
    file_format = request.form.get('file_format', 'binary')  # Значение по умолчанию: 'binary'

    # Если файл существует и имеет допустимое расширение
    if file and allowed_file(file.filename):
        # Создаем безопасное имя файла и сохраняем его
        filename = secure_filename_custom(file.filename)
        unique_name = unique_filename(filename)

        try:
            # Декодирование Base64 (если файл приходит в формате Base64)
            file_data = file.read()
            if file_format == 'base64':
                file_data = base64.b64decode(file_data)
        except Exception as e:
            return {'error': f'Error decoding file: {str(e)}'}, 400

        try:
            with open(os.path.join(app.config['UPLOAD_FOLDER'], unique_name), 'wb') as f:
                f.write(file_data)
        except Exception as e:
            return {'error': f'Error saving file: {str(e)}'}, 500

        # Создание записи в БД
        connection_info = ConnectionInfo.create(client_id=client_card, file_path=os.path.join(app.config['UPLOAD_FOLDER'], unique_name), text=text)
        connection_info.save()

        # Возвращаем сообщение об успешной загрузке файла
        return {'message': 'File uploaded and saved in the database successfully'}, 201
    else:
        # Возвращаем ошибку, если формат файла не допустим
        return {'error': 'File format not allowed'}, 400

def delete_all_connection_info(client_id):
    # Проверяем существование клиента с указанным client_id
    try:
        client_card = ClientsCard.get(ClientsCard.client_id == client_id)
    except peewee.DoesNotExist:
        return {'error': f'Client with client_id {client_id} not found'}, 404

    # Находим все записи информации о подключении для указанного клиента
    connection_info_list = ConnectionInfo.select().where(ConnectionInfo.client_id == client_card)

    if not connection_info_list:
        return {'error': f'No connection info records for client_id {client_id}'}, 404

    # Удаляем все файлы, связанные с записями
    for connection_info in connection_info_list:
        try:
            os.remove(connection_info.file_path)
        except FileNotFoundError:
            pass
        # Удаляем запись из БД
        connection_info.delete_instance()

    return jsonify({'message': f'All connection info records and related files for client_id {client_id} have been deleted'}), 200

def delete_specific_connection_info(client_id, connection_info_id):
    # Проверяем существование клиента с указанным client_id
    try:
        client_card = ClientsCard.get(ClientsCard.client_id == client_id)
    except peewee.DoesNotExist:
        return {'error': f'Client with client_id {client_id} not found'}, 404

    # Находим информацию о подключении для указанного клиента и connection_info_id
    try:
        connection_info = ConnectionInfo.get((ConnectionInfo.client_id == client_card) & (ConnectionInfo.id == connection_info_id))
    except peewee.DoesNotExist:
        return {'error': f'Connection info with connection_info_id {connection_info_id} for client_id {client_id} not found'}, 404

    # Удаляем файл, связанный с записью
    try:
        os.remove(connection_info.file_path)
    except FileNotFoundError:
        pass

    # Удаляем запись из БД
    connection_info.delete_instance()

    return jsonify({'message': f'Connection info with connection_info_id {connection_info_id} for client_id {client_id} and the related file have been deleted'}), 200
