from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from functools import wraps
from flask import request, Response

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"

# Логин и пароль для доступа к API
USERNAME = 'Njem'
PASSWORD = generate_password_hash('Rfnzkj123123')

# Создаем функцию-декоратор для аутентификации Basic Auth
def require_basic_auth(username, password):
    """Функция-декоратор принимает исходную функцию (представление) в качестве аргумента"""
    def decorator(f):
        # Используем wraps, чтобы сохранить метаданные исходной функции
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Получаем объект аутентификации из запроса
            auth = request.authorization

            # Проверяем, что аутентификация предоставлена и что имя пользователя и пароль верны
            if auth and auth.username == username and check_password_hash(password, auth.password):
                # Если аутентификация прошла успешно, выполняем исходную функцию
                return f(*args, **kwargs)
            else:
                # Если аутентификация не удалась, возвращаем ошибку 401 и заголовок WWW-Authenticate
                return Response('Authorization required', 401, {'WWW-Authenticate': 'Basic realm="Login required"'})
        
        # Возвращаем функцию, обернутую декоратором
        return decorated_function

    # Возвращаем функцию-декоратор
    return decorator
