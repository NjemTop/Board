from docxtpl import DocxTemplate
from datetime import datetime
import locale
import requests
from HappyFox.happyfox_class import HappyFoxConnector

config_file = "Main.config"

    ### ЗАПОЛНЯЕМ ТАБЛИЦУ
## перебираем тикеты и вытягиваем инфу по ним
def info_from_ticket_id(ticket_info):
    """Функция ... """
    name_of_ticket = ticket_info['subject'].replace('RE: ', '').replace('FW: ', '')
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
    if date_ticket_close is None:
        result  = 'В работе'
    else:
        result  = 'Выполнено'
    return name_of_ticket, date_ticket_start, date_ticket_close, sla, result
def create_report_tele2(contact_group_id, start_date, end_date):
    """Функция ... """
    connector = HappyFoxConnector(config_file)
    object_start_time = datetime.strptime(start_date, '%d.%m.%Y')
    start_time = object_start_time.strftime('%Y-%m-%d')
    object_end_time = datetime.strptime(end_date, '%d.%m.%Y')
    end_time = object_end_time.strftime('%Y-%m-%d')
    filtered_tickets = connector.get_filtered_tickets(start_time, end_time, contact_group_id)
    ## Создаем файл и делаем русскую локализацию для даты
    docx = DocxTemplate("./templates/Temp_report_tele2.docx")
    locale.setlocale(locale.LC_TIME, 'ru_RU.utf8')
    ### ЗАПОЛНЯЕМ ШАПКУ
    ## Находим дату (Отчет об оказанных услугах ОТ [___] )
    today = datetime.now().date().strftime('%d %B %Y')
    # Формируем общий список для добавления в файл
    table_rows = []
    # Задаем порядковый номер строки
    num = 0
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
    docx.save("./Temp_report_tele2_final.docx")

create_report_tele2(37)