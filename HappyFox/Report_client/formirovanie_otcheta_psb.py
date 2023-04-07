from docxtpl import DocxTemplate
from datetime import datetime
import locale
import requests
from datetime import datetime
from HappyFox.happyfox_class import HappyFoxConnector
import os
from pathlib import Path

config_file = "Main.config"


# Прописываем id клиента для ссылки на отчет
client_report_id = 21

## перебираем тикеты и вытягиваем инфу по ним
def info_from_ticket_id(ticket_info):
    name_of_ticket = ticket_info['subject'].replace('RE: ', '').replace('FW: ', '').replace('Fwd: ', '')
    date_ticket_start_0 = ticket_info['created_at']
    datetime_object_start = datetime.strptime(date_ticket_start_0, '%Y-%m-%d %H:%M:%S')
    date_ticket_start = datetime_object_start.strftime('%d.%m.%Y')
    date_ticket_close_0 = ticket_info['last_modified']
    datetime_object_close = datetime.strptime(date_ticket_close_0, '%Y-%m-%d %H:%M:%S')
    date_ticket_close = datetime_object_close.strftime('%d.%m.%Y')    
    ### "Нарушение сроков оказания услуг"
    sla_breaches = ticket_info['sla_breaches']
    if sla_breaches == 0:
        sla = "Нет"
    else:
        sla = "Да"
    ### "Результат услуг"
    request_type_find_id = ticket_info['custom_fields']
    request_type_find_category = ticket_info['category']
    result = ''
    if date_ticket_close is None:
        result  = 'В работе'
    else:
        for a in range(len(request_type_find_id)):
            if request_type_find_id[a].get('id') == 28:
                if request_type_find_id[a].get('value') != None:
                    if request_type_find_id[a].get('value_id') == 104:
                        result = 'Скорректирован шаблон'
                    elif request_type_find_id[a].get('value_id') == 118:
                        result = 'Передано на доработку'
                    else:
                        result = 'Консультация предоставлена'
                else:
                    result = 'Не заполнено'
            elif request_type_find_id[a].get('id') == 27:
                if request_type_find_id[a].get('value') != None:
                    result = 'Ошибка устранена'
                else:
                    result = 'Не заполнено'
            elif request_type_find_category.get('id') == 6:
                result = 'Уведомление о выходе релиза'
            else:
                continue
    return name_of_ticket, date_ticket_start, date_ticket_close, sla, result
def create_report_psb(contact_group_id, start_date, end_date):
    """Функция ... """
    connector = HappyFoxConnector(config_file)
    object_start_time = datetime.strptime(start_date, '%d.%m.%Y')
    start_time = object_start_time.strftime('%Y-%m-%d')
    object_end_time = datetime.strptime(end_date, '%d.%m.%Y')
    end_time = object_end_time.strftime('%Y-%m-%d')
    filtered_tickets = connector.get_filtered_tickets(start_time, end_time, contact_group_id)
    ## Находим дату (Отчет об оказанных услугах ОТ [___] )
    today = datetime.now().date().strftime('%d %B %Y')
    current_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    template_path = current_dir.parent.parent / 'templates' / 'Temp_report_PSB_.docx'
    ## Создаем файл и делаем русскую локализацию для даты
    docx = DocxTemplate(template_path)
    locale.setlocale(locale.LC_TIME, 'ru_RU.utf8')
    # Формируем общий список для добавления в файл
    table_rows = []
    # Задаем порядковый номер строки
    num = 0
    today = datetime.now().date().strftime('%d %B %Y')
    # Перебираем каждый тикет и создаем список (строку в таблице word)
    for ticket_info in filtered_tickets: # ticket_info - номер тикета
        name_of_ticket, date_ticket_start, date_ticket_close, sla, result = info_from_ticket_id(ticket_info) # получаем результат функции с данными по тикету
        num += 1
        # добавляем соответствие и добавляем список в table_rows
        table_rows.append({'num' : num, 'name_of_ticket' : name_of_ticket, 'date_ticket_start' : date_ticket_start, 'date_ticket_close' : date_ticket_close, 'sla' : sla, 'result' : result})
    # передаем параметры и заполняем файл
    context = {'today' : today, 'start_date': start_date, 'end_date': end_date, 'table_rows': table_rows}
    docx.render(context)
    # сохраняем файл
    docx.save("./Temp_report_PSB_final.docx")
