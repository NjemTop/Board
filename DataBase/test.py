from model_class import Report_Ticket, conn
import json
import peewee
import datetime

request = {
    "report_date": "03-05-2023",
    "ticket_id": 1234,
    "subject": "Тестовая тема",
    "create": "02-05-2023",
    "status": "Close",
    "client_name": "Название клиента",
    "priority": "Medium",
    "assignee_name": "Oleg Eliseev",
    "updated_at": "03-05-2023",
    "last_reply_at": "03-05-2023",
    "sla": False,
    "sla_time": "13 Hr, 52 Min",
    "response_time": "1 Hr, 15 Min",
    "cause": "Консультация",
    "module_boardmaps": "BoardMaps Core",
    "staff_message": 5
}

input_data = request

report_date_str = input_data['report_date']
create_str = input_data['create']
updated_at_str = input_data['updated_at']
last_reply_at_str = input_data['last_reply_at']

try:
    report_date = datetime.datetime.strptime(report_date_str, "%d-%m-%Y").date()
    create = datetime.datetime.strptime(create_str, "%d-%m-%Y").date()
    updated_at = datetime.datetime.strptime(updated_at_str, "%d-%m-%Y").date()
    last_reply_at = datetime.datetime.strptime(last_reply_at_str, "%d-%m-%Y").date()
except ValueError as e:
    print('Ошибка:', e)

# Преобразование строк с продолжительностью времени в минуты
for key in ['sla_time', 'response_time']:
    hours, minutes = map(int, input_data[key].split(' ')[::2])
    input_data[key] = hours * 60 + minutes

# Здесь мы вставляем данные в БД
with conn:
    conn.create_tables([Report_Ticket])
    new_ticket = Report_Ticket.create(**input_data)

print('Отчёт о тиете был успешно сохранён в БД')
