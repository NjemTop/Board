# coding: utf-8
import logging
from flask import Flask
from pathlib import Path
from Web_Server.web_config import USERNAME, PASSWORD, require_basic_auth
from logger.log_config import setup_logger, get_abs_log_path
from Web_Server.handler.WEB import get, create_ticket, release_data, update_ticket, yandex_oauth_callback
from Web_Server.handler.API import data_release, BM_Info_onClient, client_card, connect_card, contact_card, integration, tech_account, bm_servers_card, connection_info
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

    # Регистрация обработчика для API списка учёта версий клиентов
    app.add_url_rule('/clients_all_info/api/clients', 'get_BM_Info_onClient_api', require_basic_auth(USERNAME, PASSWORD)(BM_Info_onClient.get_BM_Info_onClient_api), methods=['GET'])
    app.add_url_rule('/clients_all_info/api/clients', 'post_BM_Info_onClient_api', require_basic_auth(USERNAME, PASSWORD)(BM_Info_onClient.post_BM_Info_onClient_api), methods=['POST'])
    app.add_url_rule('/clients_all_info/api/clients', 'patch_BM_Info_onClient_api', require_basic_auth(USERNAME, PASSWORD)(BM_Info_onClient.patch_BM_Info_onClient_api), methods=['PATCH'])
    app.add_url_rule('/clients_all_info/api/clients', 'delete_BM_Info_onClient_api', require_basic_auth(USERNAME, PASSWORD)(BM_Info_onClient.delete_BM_Info_onClient_api), methods=['DELETE'])

    # Регистрация обработчика для API списка карточек клиента
    app.add_url_rule('/clients_all_info/api/clients_card', 'get_client_card_api', require_basic_auth(USERNAME, PASSWORD)(client_card.get_client_card_api), methods=['GET'])
    # Регистрация обработчика для API с параметром id в URL
    app.route('/clients_all_info/api/client_card/<int:id>', methods=['GET'])(require_basic_auth(USERNAME, PASSWORD)(client_card.get_client_by_id))
    app.add_url_rule('/clients_all_info/api/clients_card', 'post_client_card_api', require_basic_auth(USERNAME, PASSWORD)(client_card.post_client_card_api), methods=['POST'])
    app.route('/clients_all_info/api/client_card/<int:id>', methods=['POST'])(require_basic_auth(USERNAME, PASSWORD)(client_card.post_client_card_api_by_id))
    app.route('/clients_all_info/api/client_card/<int:id>', methods=['PATCH'])(require_basic_auth(USERNAME, PASSWORD)(client_card.patch_client_card_api))
    app.add_url_rule('/clients_all_info/api/clients_card', 'delete_client_card_api', require_basic_auth(USERNAME, PASSWORD)(client_card.delete_client_card_api), methods=['DELETE'])

    # Регистрация обработчика для API списка контакта клиента
    #app.add_url_rule('/clients_all_info/api/contacts_card', 'get_contacts_api', require_basic_auth(USERNAME, PASSWORD)(get_contacts_api), methods=['GET'])
    app.route('/clients_all_info/api/contact_card/<int:id>', methods=['GET'])(require_basic_auth(USERNAME, PASSWORD)(contact_card.get_contact_by_client_id))
    #app.add_url_rule('/clients_all_info/api/contacts_card', 'post_contacts_api', require_basic_auth(USERNAME, PASSWORD)(post_contacts_api), methods=['POST'])
    app.route('/clients_all_info/api/contact_card/<int:id>', methods=['POST'])(require_basic_auth(USERNAME, PASSWORD)(contact_card.post_contact_api_by_id))
    
    # Регистрация обработчика для API информации по подключению к клиенту
    app.add_url_rule('/clients_all_info/api/connect_info', 'get_connect_info_api', require_basic_auth(USERNAME, PASSWORD)(connect_card.get_connect_info_api), methods=['GET'])
    app.route('/clients_all_info/api/connect_info/<int:id>', methods=['GET'])(require_basic_auth(USERNAME, PASSWORD)(connect_card.get_connect_info_by_id))
    app.add_url_rule('/clients_all_info/api/connect_info', 'post_connect_info_api', require_basic_auth(USERNAME, PASSWORD)(connect_card.post_connect_info_api), methods=['POST'])
    app.route('/clients_all_info/api/connect_info/<int:id>', methods=['PATCH'])(require_basic_auth(USERNAME, PASSWORD)(connect_card.patch_connect_info_api))
    app.route('/clients_all_info/api/connect_info/<int:id>', methods=['DELETE'])(require_basic_auth(USERNAME, PASSWORD)(connect_card.delete_connect_info_api))

    # Регистрация обработчика для API информация о тех УЗ клиента
    app.add_url_rule('/clients_all_info/api/tech_account/<int:client_id>', 'get_tech_account_api', require_basic_auth(USERNAME, PASSWORD)(tech_account.get_tech_account_api), methods=['GET'])
    app.add_url_rule('/clients_all_info/api/tech_account/<int:client_id>', 'post_tech_account_api', require_basic_auth(USERNAME, PASSWORD)(tech_account.post_tech_account_api), methods=['POST'])
    app.add_url_rule('/clients_all_info/api/tech_account/<int:client_id>', 'patch_tech_account_api', require_basic_auth(USERNAME, PASSWORD)(tech_account.patch_tech_account_api), methods=['PATCH'])
    app.add_url_rule('/clients_all_info/api/tech_account/<int:client_id>', 'delete_tech_account_api', require_basic_auth(USERNAME, PASSWORD)(tech_account.delete_tech_account_api), methods=['DELETE'])

    # Регистрация обработчика для API информация о серверах клиента
    app.add_url_rule('/clients_all_info/api/bm_servers_card/<int:client_id>', 'get_bm_servers_card_api', require_basic_auth(USERNAME, PASSWORD)(bm_servers_card.get_bm_servers_card_api), methods=['GET'])
    app.add_url_rule('/clients_all_info/api/bm_servers_card/<int:client_id>', 'post_bm_servers_card_api', require_basic_auth(USERNAME, PASSWORD)(bm_servers_card.post_bm_servers_card_api), methods=['POST'])

    # Регистрация обработчика для API информация об интеграции клиента
    app.add_url_rule('/clients_all_info/api/integration/<int:client_id>', 'get_integration_api', require_basic_auth(USERNAME, PASSWORD)(integration.get_integration_api), methods=['GET'])
    app.add_url_rule('/clients_all_info/api/integration/<int:client_id>', 'post_integration_api', require_basic_auth(USERNAME, PASSWORD)(integration.post_integration_api), methods=['POST'])
    app.add_url_rule('/clients_all_info/api/integration/<int:client_id>', 'patch_integration_api', require_basic_auth(USERNAME, PASSWORD)(integration.patch_integration_api), methods=['PATCH'])

    # Регистрация обработчика для API информация о настройки подключения к клиенту
    app.add_url_rule('/clients_all_info/api/connection_info/<int:client_id>', 'get_uploaded_conn_files', require_basic_auth(USERNAME, PASSWORD)(connection_info.get_uploaded_conn_files), methods=['GET'])
    app.add_url_rule('/clients_all_info/api/connection_info/clients/<int:client_id>/file', 'get_serve_file', require_basic_auth(USERNAME, PASSWORD)(connection_info.get_serve_file), methods=['GET'])
    app.add_url_rule('/clients_all_info/api/connection_info/<int:client_id>', 'post_upload_conn_file', require_basic_auth(USERNAME, PASSWORD)(connection_info.post_upload_conn_file), methods=['POST'])
    app.add_url_rule('/clients_all_info/api/connection_info/<int:client_id>', 'delete_upload_conn_file', require_basic_auth(USERNAME, PASSWORD)(connection_info.delete_connection_info), methods=['DELETE'])
    
    return app

if __name__ == '__main__':
    try:
        server_address = ('0.0.0.0', 3030)
        app = create_app()
        web_info_logger.info('Сервер запущен. Порт работы: %s', server_address[1])
        app.run(host=server_address[0], port=server_address[1], debug=True)
    except Exception as error_message:
        web_error_logger.error("Ошибка при запуске ВЭБ-сервера: %s", error_message)
        raise error_message
