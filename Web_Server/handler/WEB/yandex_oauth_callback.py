from flask import request, Response
import requests
import json
import logging
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"

# Читаем данные из файла
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    DATA = json.load(file)

# Получаем значение ключа CLIENT_ID и CLIENT_SECRET в YANDEX_DISK
CLIENT_ID = DATA['YANDEX_DISK']['CLIENT_ID']
CLIENT_SECRET = DATA['YANDEX_DISK']['CLIENT_SECRET']

def handler_get_yandex_oauth_callback():
        """Функция определения oauth яндекса"""
        # Извлеките авторизационный код из URL
        authorization_code = request.args.get('code')
        print(authorization_code)
        if not authorization_code:
            return Response('Ошибка: авторизационный код не найден', mimetype='text/plain')

        # Запросите OAuth-токен, используя авторизационный код
        token_request_data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": "8525a645d7744d008ea42465c080b2a7",
            "client_secret": "1b9335d34574471b894d1c2576305a11",
            "redirect_uri": "/yandex_oauth_callback"
        }
        token_response = requests.post('https://oauth.yandex.ru/token', data=token_request_data, timeout=30)

        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data['access_token']

            # Отправляем в ответ браузера access_token, который нужно сохранить
            return Response(f'OAuth-токен успешно получен: {access_token}', mimetype='text/plain')
        # Если ошибка, отправим её
        return Response('Ошибка: не удалось получить OAuth-токен', mimetype='text/plain', status=400)