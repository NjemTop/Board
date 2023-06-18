from docxtpl import DocxTemplate
from datetime import datetime
import locale
import requests
from datetime import datetime

# Прописываем id клиента для ссылки на отчет
client_report_id = 11
############################## ШАБЛОН ДЛЯ ТЕЛЕ2
## Создаем файл и делаем русскую локализацию для даты
docx = DocxTemplate("Temp_report_PSB.docx")
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
### Авторизация в HappyFox
# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"
# Открываем файл и загружаем данные
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
    data_config = json.load(f)
# Извлекаем значения API_KEY и API_SECRET
API_ENDPOINT = data_config['HAPPYFOX_SETTINGS']['API_ENDPOINT']
API_KEY = data_config['HAPPYFOX_SETTINGS']['API_KEY']
API_SECRET = data_config['HAPPYFOX_SETTINGS']['API_SECRET']
# Прохождение кол-ва страниц по url первой страницы
headers = {'Content-Type': 'application/json'}
param = {'period_type' : 'srp'}
url_0 = f"https://boardmaps.happyfox.com/api/1.1/json/report/{client_report_id}/tabulardata/?size=50&page=1"
res_0 = requests.get(url_0, auth=(API_KEY, API_SECRET), headers=headers, params=param).json()
#находим кол-во страниц
pages_len = res_0.get('page_count')
### ЗАПОЛНЯЕМ ШАПКУ
## Находим дату (Отчет об оказанных услугах ОТ [___] )
today = datetime.now().date().strftime('%d %B %Y')
# start_date
# end_date
### ЗАПОЛНЯЕМ ТАБЛИЦУ
## перебираем страницы и вытягиваем инфу по айди тикета
def list_of_rows(client_report_id, pages_len):
    list = []
    for page in range(1, pages_len + 1):
        url = f"https://boardmaps.happyfox.com/api/1.1/json/report/{client_report_id}/tabulardata/?size=50&page={page}"
        res = requests.get(url, auth=auth, headers=headers, params=param).json()
        get_rows = res.get('rows')
        for j in range(len(get_rows)):
            get_id = get_rows[j].get('id')
            list.append(get_id)
    return list
## перебираем тикеты и вытягиваем инфу по ним
def info_from_ticket_id(ticket_id):
    url = f"https://boardmaps.happyfox.com/api/1.1/json/ticket/{ticket_id}"
    res = requests.get(url, auth=auth, headers=headers, params=param).json()
    name_of_ticket = (res.get('subject')).replace('RE: ', '').replace('FW: ', '')
    date_ticket_start_0 = res.get('created_at')
    datetime_object_start = datetime.strptime(date_ticket_start_0, '%Y-%m-%d %H:%M:%S')
    date_ticket_start = datetime_object_start.strftime('%d.%m.%Y')
    date_ticket_close_0 = res.get('last_modified')
    datetime_object_close = datetime.strptime(date_ticket_close_0, '%Y-%m-%d %H:%M:%S')
    date_ticket_close = datetime_object_close.strftime('%d.%m.%Y')    
    ### "Нарушение сроков оказания услуг"
    sla_breaches = res.get('sla_breaches')
    if sla_breaches == 0:
        sla = "Нет"
    else:
        sla = "Да"
    ### "Результат услуг"
    request_type_find_id = res.get('custom_fields')
    request_type_find_category = res.get('category')
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
# Номера тикетов для вывода в файл
all_tickets_id_list = list_of_rows(client_report_id, pages_len)
# Формируем общий список для добавления в файл
table_rows = []
# Задаем порядковый номер строки
num = 0
# Перебираем каждый тикет и создаем список (строку в таблице word)
for ticket_id in all_tickets_id_list: # ticket_id - номер тикета
    name_of_ticket, date_ticket_start, date_ticket_close, sla, result = info_from_ticket_id(ticket_id) # получаем результат функции с данными по тикету
    num += 1
    # добавляем соответствие и добавляем список в table_rows
    table_rows.append({'today' : today, 'num' : num, 'name_of_ticket' : name_of_ticket, 'date_ticket_start' : date_ticket_start, 'date_ticket_close' : date_ticket_close, 'sla' : sla, 'result' : result})
# передаем параметры и заполняем файл
context = {'today' : today, 'table_rows': table_rows}
docx.render(context)
# сохраняем файл
docx.save("./Temp_report_PSB_final.docx")
