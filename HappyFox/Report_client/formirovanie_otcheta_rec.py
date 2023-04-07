from docxtpl import DocxTemplate
import locale
import requests
from datetime import datetime
import subprocess, sys
from Report_client.formirovanie_otcheta_tele2 import list_of_rows

# Прописываем id клиента для ссылки на отчет
client_report_id = 12
## Создаем файл и делаем русскую локализацию для даты
docx = DocxTemplate("./templates/Temp_report_REC.docx")
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
## Авторизация в HappyFox и нахождение кол-ва страниц по url первой страницы
auth = ('45357d176a5f4e25b740aebae58f189c','3b9e5c6cc6f34802ad5ae82bafdab3bd')
headers = {'Content-Type': 'application/json'}
param = {'period_type' : 'srp'}
url_0 = f"https://boardmaps.happyfox.com/api/1.1/json/report/{client_report_id}/tabulardata/?size=50&page=1"
res_0 = requests.get(url_0,auth=auth, headers=headers, params=param).json()
#находим кол-во страниц
pages_len = res_0.get('page_count')
### ЗАПОЛНЯЕМ ШАПКУ
## Находим дату (Отчет об оказанных услугах ОТ [___] )
today = datetime.now().date().strftime('%d %B %Y')
# start_date
# end_date

# Номера тикетов для вывода в файл
all_tickets_id_list = list_of_rows(client_report_id, pages_len, auth, headers, param)

## перебираем тикеты и вытягиваем инфу по ним
def info_from_ticket_id(ticket_id):
    url = f"https://boardmaps.happyfox.com/api/1.1/json/ticket/{ticket_id}"
    res = requests.get(url, auth=auth, headers=headers, params=param).json()
    # Полный номер заявки
    display_id = res.get('display_id')
    # Услуга = тип обращения
    request_type_find_id = res.get('custom_fields')
    request_type = ''
    for a in range(len(request_type_find_id)):
        if request_type_find_id[a].get('id') == 21:
            if request_type_find_id[a].get('value') != None:
                request_type = request_type_find_id[a].get('value')
            else:
                request_type = 'Не заполнено'
        else:
            continue
    # Уровень критичности + Плановое время реакции (first_resp_plan) + Плановое время решения (full_resp_plan)
    priority_eng = res.get('priority').get('name')
    if priority_eng == 'Low':
        priority = 'Низкий'
        first_resp_plan = '16:00'
        full_resp_plan = '240:00'
    elif priority_eng == 'Medium':
        priority = 'Средний'
        first_resp_plan = '08:00'
        full_resp_plan = '80:00'
    elif priority_eng == 'High':
        priority = 'Высокий'
        first_resp_plan = '05:00'
        full_resp_plan = '40:00'
    elif priority_eng == 'Critical':
        priority = 'Критический'
        first_resp_plan = '03:00'
        full_resp_plan = '24:00'
    else:
        priority = 'Не установлен'
        first_resp_plan = 'Не установлен'
        full_resp_plan = 'Не установлен'
    # Ответственный client_user
    client_user = res.get('user').get('name')
    # Краткое описание заявки = тема тикета
    subject = (res.get('subject')).replace('RE: ', '').replace('FW: ', '')
    # Текущий статус заявки + Дата решения заявки 
    status_eng = res.get('status').get('name')
    if status_eng == 'Closed':
        status = 'Закрыт'
        date_ticket_close_0 = res.get('last_modified')
        datetime_object_close = datetime.strptime(date_ticket_close_0, '%Y-%m-%d %H:%M:%S')
        date_ticket_close = datetime_object_close.strftime('%d.%m.%Y')
    else:
        status = 'В работе'
        date_ticket_close = '-'
    # Дата регистрации заявки 
    date_ticket_start_0 = res.get('created_at')
    datetime_object_start = datetime.strptime(date_ticket_start_0, '%Y-%m-%d %H:%M:%S')
    date_ticket_start = datetime_object_start.strftime('%d.%m.%Y')
    # Фактическое время решения fact_resp_time
    setup_script = 'Response_time_2.ps1'
    result = subprocess.run([ "pwsh", "-File", setup_script, str(ticket_id) ], capture_output=True, text=True)
    fact_resp_time = str(result.stdout).rstrip()
    # Превышение планового времени решения sla
    sla_breaches = res.get('sla_breaches')
    if sla_breaches == 0:
        sla = "Нет"
    else:
        sla = "Да"
    
    return display_id, request_type, priority, client_user, subject, status, date_ticket_start, date_ticket_close, first_resp_plan, full_resp_plan, fact_resp_time, sla

# Формируем общий список для добавления в файл
table_rows = []
# Перебираем каждый тикет и создаем список (строку в таблице word)
for ticket_id in all_tickets_id_list:
    # получаем результат функции с данными по тикету
    display_id, request_type, priority, client_user, subject, status, date_ticket_start, date_ticket_close, first_resp_plan, full_resp_plan, fact_resp_time, sla = info_from_ticket_id(ticket_id)
    # добавляем соответствие и добавляем список в table_rows
    table_rows.append({'today' : today, 'display_id' : display_id, 'request_type' : request_type, 'priority' : priority, 'client_user' : client_user, 'subject' : subject, 
        'status' : status, 'date_ticket_start' : date_ticket_start, 'date_ticket_close' : date_ticket_close, 'first_resp_plan' : first_resp_plan, 'full_resp_plan' : full_resp_plan, 
        'fact_resp_time' : fact_resp_time, 'sla' : sla})
# передаем параметры и заполняем файл
context = {'today' : today, 'table_rows': table_rows}
docx.render(context)
# сохраняем файл
docx.save("./Report_client/Temp_report_REC_final.docx")
