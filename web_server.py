# coding: utf-8
import logging
from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
from pathlib import Path
from Web_Server.web_config import USERNAME, PASSWORD, require_basic_auth
from logger.log_config import setup_logger, get_abs_log_path
from Web_Server.handler.WEB import get, create_ticket, release_data, update_ticket, yandex_oauth_callback, report
from Web_Server.handler.API import data_release
from DataBase import migrations
from Web_Server.handler.API.connection_info import init_app

# Указываем настройки логов для нашего файла с классами
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def create_app():
    """Функция создания приложения ВЭБ-сервера"""
    app = Flask(__name__)
    init_app(app)
    config_file = Path(__file__).parent / 'Web_Server' / 'web_config.py'
    app.config.from_pyfile(config_file)

    # Настройка конфигурации Swagger
    SWAGGER_URL = '/swagger'
    API_URL = '/static/swagger.json'

    # Регистрация схемы Swagger
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Вэб-сервер"
        }
    )

    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # Регистрация обработчиков для URL 
    app.add_url_rule('/', 'handler_get', get.handler_get, methods=['GET'])

    # Регистрация обработчиков для URL /create_ticket
    app.add_url_rule('/create_ticket', 'handler_get_create_ticket', create_ticket.handler_get_create_ticket, methods=['GET'])
    app.add_url_rule('/create_ticket', 'handler_post_create_ticket', create_ticket.handler_post_create_ticket, methods=['POST'])

    # Регистрация обработчиков для URL /update_ticket
    app.add_url_rule('/update_ticket', 'handler_get_update_ticket', update_ticket.handler_get_update_ticket, methods=['GET'])
    app.add_url_rule('/update_ticket', 'handler_post_update_ticket', update_ticket.handler_post_update_ticket, methods=['POST'])

    # Регистрация обработчиков для URL /undersponed_ticket
    app.add_url_rule('/undersponed_ticket', 'handler_undersponed_ticket', update_ticket.handler_undersponed_ticket, methods=['POST'])

    # Регистрация обработчиков для URL с узнаванием OAuth яндекса (токена авторизации)
    app.add_url_rule('/yandex_oauth_callback', 'handler_get_yandex_oauth_callback', yandex_oauth_callback.handler_get_yandex_oauth_callback, methods=['GET'])

    # Регистрация обработчиков для API со списком версий отправки релиза
    app.add_url_rule('/data_release/api/versions', 'api_data_release_versions', data_release.api_data_release_versions, methods=['GET'])
    # Регистрация обработчика для API с параметром version в URL
    app.route('/data_release/api/<string:version>', methods=['GET'])(require_basic_auth(USERNAME, PASSWORD)(data_release.api_data_release_number))
    # Регистрация обработчиков для URL спика всех отправленных версиях
    app.add_url_rule('/data_release', 'data_release_html', release_data.data_release_html, methods=['GET'])

    # Регистрация обработчиков для вывода информации о статистике (диаграммы/пироги)
    app.add_url_rule('/report', 'report_tickets', report.report_tickets, methods=['GET'])
    app.add_url_rule('/api/web/report', 'post_api_report_tickets', report.post_api_report_tickets, methods=['POST'])
    app.add_url_rule('/api/report', 'get_report_tickets', require_basic_auth(USERNAME, PASSWORD)(report.get_report_tickets), methods=['GET'])
    app.add_url_rule('/api/report', 'post_report_tickets', require_basic_auth(USERNAME, PASSWORD)(report.post_report_tickets), methods=['POST'])

    return app

if __name__ == '__main__':
    try:
        # Запусск вэб-сервера
        server_address = ('0.0.0.0', 3030)
        app = create_app()

        # # Запуск миграций и логирование
        # try:
        #     migrations.create_migrations()
        #     web_info_logger.info("Миграции успешно выполнены")
        # except Exception as migration_error:
        #     web_error_logger.error("Ошибка при выполнении миграций: %s", migration_error)
        #     raise migration_error

        web_info_logger.info('Сервер запущен. Порт работы: %s', server_address[1])
        app.run(host=server_address[0], port=server_address[1], debug=True)
    except Exception as error_message:
        web_error_logger.error("Ошибка при запуске ВЭБ-сервера: %s", error_message)
        raise error_message
