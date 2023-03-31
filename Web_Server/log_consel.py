from flask import request

class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, resp):
        # Получаем данные о текущем запросе
        path = request.path
        method = request.method
        headers = dict(request.headers)
        user_agent = headers.get('User-Agent', '-')
        remote_addr = environ.get('HTTP_X_FORWARDED_FOR', environ.get('REMOTE_ADDR'))
        http_version = environ.get('SERVER_PROTOCOL')
        content_length = headers.get('Content-Length', '-')

        # Логируем информацию о запросе
        self.app.logger.info(f'{remote_addr} - "{method} {path} {http_version}" {resp.status_code} {content_length} "{user_agent}"')
        return resp
