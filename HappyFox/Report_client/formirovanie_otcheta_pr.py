from docxtpl import DocxTemplate
from datetime import datetime
import locale
import requests
from HappyFox.happyfox_class import HappyFoxConnector
import os
from pathlib import Path
import subprocess

config_file = "Main.config"

# Прописываем id клиента для ссылки на отчет
client_report_id = 9

    ### ЗАПОЛНЯЕМ ТАБЛИЦУ
## перебираем тикеты и вытягиваем инфу по ним
def info_from_ticket_info(ticket_info):
    # Полный номер заявки
    display_id = ticket_info['display_id']
    # Дата создания тикета
    date_ticket_start_0 = ticket_info['created_at']
    datetime_object_start = datetime.strptime(date_ticket_start_0, '%Y-%m-%d %H:%M:%S')
    date_ticket_start = str(datetime_object_start.strftime('%d.%m.%Y'))
    # Дата закрытия тикета
    date_ticket_close_0 = ticket_info['last_modified']
    datetime_object_close = datetime.strptime(date_ticket_close_0, '%Y-%m-%d %H:%M:%S')
    date_ticket_close = str(datetime_object_close.strftime('%d.%m.%Y')) 
    # Вид запроса 
    request_type = 'request_type'
    # Тема 
    subject = ticket_info['subject'].replace('RE: ', '').replace('FW: ', '').replace('Fwd: ', '')
    # Заявитель
    client_user = ticket_info['user'].get['name']
    # Статус 
    status_eng = ticket_info['status'].get['name']
    if status_eng == 'Closed':
        status = 'Закрыт'
    else:
        status = 'В работе'
    # Время решения тикета + конвертация в минуты fact_resp_time
    setup_script = './Response_time_2.ps1'
    result_time = subprocess.run([ "pwsh", "-File", setup_script, str(ticket_info)], capture_output=True, text=True)
    fact_resp_time = str(result_time.stdout).rstrip()
    # Приоритет
    priority_eng = ticket_info['priority'].get('name')
    if priority_eng == 'Low':
        priority = 'Низкий'
    elif priority_eng == 'Medium':
        priority = 'Средний'
    elif priority_eng == 'High':
        priority = 'Высокий'
    elif priority_eng == 'Critical':
        priority = 'Критический'
    else:
        priority = 'Не установлен'

    return display_id, date_ticket_start, date_ticket_close, request_type, subject, client_user, status, fact_resp_time, priority, date_ticket_start_0

def create_report_psb(contact_group_id, start_date, end_date, template_path):
    """Функция ... """
    connector = HappyFoxConnector(config_file)
    object_start_time = datetime.strptime(start_date, '%d.%m.%Y')
    start_time = object_start_time.strftime('%Y-%m-%d')
    object_end_time = datetime.strptime(end_date, '%d.%m.%Y')
    end_time = object_end_time.strftime('%Y-%m-%d')
    filtered_tickets = connector.get_filtered_tickets(start_time, end_time, contact_group_id)
    ## Находим дату (Отчет об оказанных услугах ОТ [___] )
    today = datetime.now().date().strftime('%d %B %Y')
    ## Создаем файл и делаем русскую локализацию для даты
    docx = DocxTemplate(template_path)
    locale.setlocale(locale.LC_TIME, 'ru_RU.utf8')
    today = datetime.now().date().strftime('%d %B %Y')
    # Формируем общий список для добавления в файл
    table_rows = []
    # Задаем порядковый номер строки
    num = 0
    
    # Счетчик общего кол-ва запросов
    len_tickets_list_28 = 0
    # Счетчик общего кол-ва инцедентов
    len_tickets_list_27 = 0
    # Счетчики на "Зарегистрировано в отчетный период Запросы на обслуживание" по приоритетам
    len_tickets_list_28_H = 0
    len_tickets_list_28_M = 0
    len_tickets_list_28_L = 0
    # Счетчики на "Зарегистрировано в отчетный период Инциденты" по приоритетам
    len_tickets_list_27_C = 0
    len_tickets_list_27_H = 0
    len_tickets_list_27_M = 0
    len_tickets_list_27_L = 0

    # Счетчик общего кол-ва запросов
    len_tickets_list_28_old = 0
    # Счетчик общего кол-ва инцедентов
    len_tickets_list_27_old = 0
    # Счетчики на "Зарегистрировано в отчетный период Запросы на обслуживание" по приоритетам
    len_tickets_list_28_H_old = 0
    len_tickets_list_28_M_old = 0
    len_tickets_list_28_L_old = 0
    # Счетчики на "Зарегистрировано в отчетный период Инциденты" по приоритетам
    len_tickets_list_27_C_old = 0
    len_tickets_list_27_H_old = 0
    len_tickets_list_27_M_old = 0
    len_tickets_list_27_L_old = 0
    # Перешло с прошлого периода всего 
    len_tickets_list_old = len_tickets_list_28_old + len_tickets_list_27_old

    # Перебираем каждый тикет и создаем список (строку в таблице word)
    new_tickets_list = []
    old_tickets_list = []
    for ticket_info in filtered_tickets:
        # получаем результат функции с данными по тикету
        display_id, date_ticket_start, date_ticket_close, request_type, subject, client_user, status, fact_resp_time, priority, date_ticket_start_0 = info_from_ticket_info(ticket_info)
        num += 1
        # добавляем соответствие и добавляем список в table_rows
        table_rows.append({'num': num, 'display_id' : display_id, 'date_ticket_start' : date_ticket_start, 'date_ticket_close' : date_ticket_close, 'request_type' : request_type,
        'subject' : subject, 'client_user' : client_user, 'status' : status, 'fact_resp_time' : fact_resp_time, 'priority' : priority})
        request_type_find_id = ticket_info.get['custom_fields']
        request_type = ''
        if date_ticket_start_0 >= start_date:
            for a in range(len(request_type_find_id)):
                priority_27_28 = ticket_info.get['priority'].get['name']
                # Зарегистрировано в отчетный период Запросы на обслуживание
                if request_type_find_id[a].get('id') == 28:
                    len_tickets_list_28 += 1
                    new_tickets_list.append(ticket_info)
                    # Зарегистрировано в отчетный период Запросы на обслуживание Высокий
                    if priority_27_28 == 'High':
                        len_tickets_list_28_H += 1
                    # Зарегистрировано в отчетный период Запросы на обслуживание Средний
                    elif priority_27_28 == 'Medium':
                        len_tickets_list_28_M += 1
                    # Зарегистрировано в отчетный период Запросы на обслуживание Низкий
                    elif priority_27_28 == 'Low':
                        len_tickets_list_28_L += 1
                # Зарегистрировано в отчетный период Инциденты len_tickets_list_27
                elif request_type_find_id[a].get('id') == 27:
                    len_tickets_list_27 += 1
                    new_tickets_list.append(ticket_info)
                    # Зарегистрировано в отчетный период Инциденты Критичный len_tickets_list_27_C
                    if priority_27_28 == 'Critical':
                        len_tickets_list_27_C += 1
                    # Зарегистрировано в отчетный период Инциденты Высокий len_tickets_list_27_H
                    elif priority_27_28 == 'High':
                        len_tickets_list_27_H += 1
                    # Зарегистрировано в отчетный период Инциденты Средний len_tickets_list_27_M 
                    elif priority_27_28 == 'Medium':
                        len_tickets_list_27_M += 1
                    # Зарегистрировано в отчетный период Инциденты Низкий len_tickets_list_27_L
                    elif priority_27_28 == 'Low':
                        len_tickets_list_27_L += 1
                else:
                    continue
        elif date_ticket_start_0 < start_date:
            for b in range(len(request_type_find_id)):
                priority_27_28_old = ticket_info.get['priority'].get['name']
                # Перешло с прошлого периода Запросы на обслуживание len_tickets_list_28_old 
                if request_type_find_id[b].get('id') == 28:
                    len_tickets_list_28_old += 1
                    old_tickets_list.append(ticket_info)
                    # Перешло с прошлого периода Запросы на обслуживание Высокий len_tickets_list_28_H_old
                    if priority_27_28_old == 'High':
                        len_tickets_list_28_H_old += 1
                    # Перешло с прошлого периода Запросы на обслуживание Средний len_tickets_list_28_M_old
                    elif priority_27_28_old == 'Medium':
                        len_tickets_list_28_M_old += 1
                    # Перешло с прошлого периода Запросы на обслуживание Низкий len_tickets_list_28_L_old
                    elif priority_27_28_old == 'Low':
                        len_tickets_list_28_L_old += 1
                # Перешло с прошлого периода Инциденты len_tickets_list_27_old 
                elif request_type_find_id[b].get('id') == 27:
                    len_tickets_list_27_old += 1
                    old_tickets_list.append(ticket_info)
                    # Перешло с прошлого периода Инциденты Критичный len_tickets_list_27_C_old
                    if priority_27_28_old == 'Critical':
                        len_tickets_list_27_C_old += 1
                    # Перешло с прошлого периода Инциденты Высокий len_tickets_list_27_H_old
                    elif priority_27_28_old == 'High':
                        len_tickets_list_27_H_old += 1
                    # Перешло с прошлого периода Инциденты Средний len_tickets_list_27_M_old
                    elif priority_27_28_old == 'Medium':
                        len_tickets_list_27_M_old += 1
                    # Перешло с прошлого периода Инциденты Низкий len_tickets_list_27_L_old 
                    elif priority_27_28_old == 'Low':
                        len_tickets_list_27_L_old += 1
                else:
                    continue
        else:
            print('Ошибка')
    
    
    
    # Выполнено в срок всего len_tickets_list_1
    # Выполнено в срок Запросы на обслуживание len_tickets_list_28_1
    # Выполнено в срок Запросы на обслуживание Высокий len_tickets_list_28_H_1
    # Выполнено в срок Запросы на обслуживание Средний len_tickets_list_28_M_1
    # Выполнено в срок Запросы на обслуживание Низкий len_tickets_list_28_L_1
    # Выполнено в срок Инциденты len_tickets_list_27_1
    # Выполнено в срок Инциденты Критичный len_tickets_list_27_C_1
    # Выполнено в срок Инциденты Высокий len_tickets_list_27_H_1
    # Выполнено в срок Инциденты Средний len_tickets_list_27_M_1
    # Выполнено в срок Инциденты Низкий len_tickets_list_27_L_1

    # Закрыто с нарушением срока всего len_tickets_list_2
    # Закрыто с нарушением срока Запросы на обслуживание len_tickets_list_28_2
    # Закрыто с нарушением срока Запросы на обслуживание Высокий len_tickets_list_28_H_2
    # Закрыто с нарушением срока Запросы на обслуживание Средний len_tickets_list_28_M_2
    # Закрыто с нарушением срока Запросы на обслуживание Низкий len_tickets_list_28_L_2
    # Закрыто с нарушением срока Инциденты len_tickets_list_27_2
    # Закрыто с нарушением срока Инциденты Критичный len_tickets_list_27_C_2
    # Закрыто с нарушением срока Инциденты Высокий len_tickets_list_27_H_2
    # Закрыто с нарушением срока Инциденты Средний len_tickets_list_27_M_2
    # Закрыто с нарушением срока Инциденты Низкий len_tickets_list_27_L_2

    # Выполняется без нарушения срока всего len_tickets_list_3
    # Выполняется без нарушения срока Запросы на обслуживание len_tickets_list_28_3
    # Выполняется без нарушения срока Запросы на обслуживание Высокий len_tickets_list_28_H_3
    # Выполняется без нарушения срока Запросы на обслуживание Средний len_tickets_list_28_M_3
    # Выполняется без нарушения срока Запросы на обслуживание Низкий len_tickets_list_28_L_3
    # Выполняется без нарушения срока Инциденты len_tickets_list_27_3
    # Выполняется без нарушения срока Инциденты Критичный len_tickets_list_27_C_3
    # Выполняется без нарушения срока Инциденты Высокий len_tickets_list_27_H_3
    # Выполняется без нарушения срока Инциденты Средний len_tickets_list_27_M_3
    # Выполняется без нарушения срока Инциденты Низкий len_tickets_list_27_L_3

    # Выполняется с нарушением срока всего len_tickets_list_4
    # Выполняется с нарушением срока Запросы на обслуживание len_tickets_list_28_4
    # Выполняется с нарушением срока Запросы на обслуживание Высокий len_tickets_list_28_H_4
    # Выполняется с нарушением срока Запросы на обслуживание Средний len_tickets_list_28_M_4
    # Выполняется с нарушением срока Запросы на обслуживание Низкий len_tickets_list_28_L_4
    # Выполняется с нарушением срока Инциденты len_tickets_list_27_4
    # Выполняется с нарушением срока Инциденты Критичный len_tickets_list_27_C_4
    # Выполняется с нарушением срока Инциденты Высокий len_tickets_list_27_H_4
    # Выполняется с нарушением срока Инциденты Средний len_tickets_list_27_M_4
    # Выполняется с нарушением срока Инциденты Низкий len_tickets_list_27_L_4

    # Процент SLA всего len_tickets_list_result
    # Процент SLA Запросы на обслуживание len_tickets_list_28_result
    # Процент SLA Запросы на обслуживание Высокий len_tickets_list_28_H_result
    # Процент SLA Запросы на обслуживание Средний len_tickets_list_28_M_result
    # Процент SLA Запросы на обслуживание Низкий len_tickets_list_28_L_result
    # Процент SLA Инциденты len_tickets_list_27_result
    # Процент SLA Инциденты Критичный len_tickets_list_27_C_result
    # Процент SLA Инциденты Высокий len_tickets_list_27_H_result
    # Процент SLA Инциденты Средний len_tickets_list_27_M_result
    # Процент SLA Инциденты Низкий len_tickets_list_27_L_result

    # передаем параметры и заполняем файл
    print('Запись файла в документ')
    context = {'today' : today, 'start_date': start_date, 'end_date': end_date, 'table_rows' : table_rows}
    docx.render(context)
    # сохраняем файл
    print('*****************************************')
    print('Сохранение файла')
    docx.save("./Temp_report_PR_final.docx")
