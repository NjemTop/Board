from flask import request, Response
import logging
import json
from Web_Server.function import parse_json_message, handle_client_reply, handle_assignee_change, handle_unresponded_info_60, handle_unresponded_info_120, handle_unresponded_info_180
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
web_error_logger = setup_logger('WebError', get_abs_log_path('web-errors.log'), logging.ERROR)
web_info_logger = setup_logger('WebInfo', get_abs_log_path('web-info.log'), logging.INFO)

def handler_get_update_ticket():
        """Функция обработки GET запросов по URL"""
        ip_address = f"Request from {request.remote_addr}: {request.url}"
        user_agent = request.headers.get('User-Agent')
        user_who = f'User-Agent: {user_agent}'
        web_info_logger.info('Кто-то зашёл на сайт c IP-адреса: %s', ip_address)
        web_info_logger.info('Его данные подключения: %s', (user_who,))
        return Response('Этот URL для получение вэбхуков (обнова)', mimetype='text/plain')

def handler_post_update_ticket():
        """Функция обработки обновления тикета из HappyFox"""
        try:
            message = request.data.decode('utf-8')
            json_data, error = parse_json_message(message)
            if error:
                return Response(error, status=400)
            
            if json_data.get("update") is None:
                return Response(status=200)
            
            json_message_type = json_data["update"].get("message_type")
            if json_message_type == "Client Reply":
                result, error = handle_client_reply(json_data)
            elif json_data["update"].get("assignee_change") is not None:
                result, error = handle_assignee_change(json_data)
            elif "by" in json_data["update"] and json_data["update"].get("by").get("type") == "smartrule":
                if json_data["update"].get("by").get("name") == "Unresponded for 60 min":
                    result, error = handle_unresponded_info_60(json_data)
                elif json_data["update"].get("by").get("name") == "Unresponded for 120 min":
                    result, error = handle_unresponded_info_120(json_data)
                elif json_data["update"].get("by").get("name") == "Unresponded for 180 min":
                    result, error = handle_unresponded_info_180(json_data)
                else:
                    return Response(status=200)
            else:
                return Response(status=200)
            
            if error:
                return Response(error, status=400)
            return Response(result, status=201)
        except Exception as error_message:
            web_error_logger.error("Ошибка при обработке обновления тикета: %s", str(error_message))
            return Response("Ошибка на сервере", status=500)

def handler_undersponed_ticket():
        """Функция обработки вебхука от HappyFox, если тикет был отложен"""
        message = ""
        message = request.data.decode('utf-8')
        try:
            # находим JSON в сообщении
            json_start = message.find('{')
            if json_start != -1:
                json_str = message[json_start:]
                # парсим JSON
                json_data = json.loads(json_str)
                print(json_data)
                web_info_logger.info('Направлена информация в группу о созданном тикете: %s', json_data)
            else:
                web_error_logger.error("JSON не найден в сообщении. %s")
                return 'JSON не найден в сообщении.', 400
        except ValueError as error_message:
            web_error_logger.error("Не удалось распарсить JSON в запросе. %s", error_message)
            return 'Не удалось распарсить JSON в запросе.', 500
        
        # Отправляем ответ о том, что всё принято и всё хорошо
        return "OK", 201
