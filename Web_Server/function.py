import json
import logging
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def parse_json_message(message):
    """Функция парсинга JSON-строки"""
    try:
        # проверяем наличие JSON в сообщении
        if '{' not in message:
            web_error_logger.error("JSON не найден в сообщении. %s")
            return None, 'JSON не найден в сообщении.'
        # находим JSON в сообщении
        json_start = message.find('{')
        if json_start != -1:
            json_str = message[json_start:]
        else:
            web_error_logger.error("JSON не найден в сообщении. %s")
            return None, 'JSON не найден в сообщении.'
        # парсим JSON
        json_data = json.loads(json_str)
        return json_data, None
    except ValueError as error_message:
        web_error_logger.error("Не удаётся распарсить JSON в запросе. %s", error_message)
        return None, 'Не удаётся распарсить JSON в запросе.'