import pandas as pd
import locale
from datetime import datetime
import sqlite3

def upload_db_result(version_number, result):
    # Запись месяца в дате по-русски
    # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
    # Определяем дату рассылки = текущапя дата запуска скрипта
    today = datetime.now().date().strftime('%d %B %Y')

    # Составляем словарь для сбора данных:
    map = {}
    id = 0
    result_db = []
    # Создаем из построчного вывода общий список
    item = result.split('\n')
    # Перебираем списки внутри общего списка
    for i in item:
        # Исключаем пустой список
        if i != '':
            # Делим список по параметрам с пом. разделителя
            l = i.split('|')
            id += 1
            map[id] = {}
            # Наименование клиента
            client_name = l[0]
            # Основной контакт
            main_contact = l[1]
            # Копия
            if len(l) == 3:
                copy_contact = l[2].replace(',', ', ')
            else:
                copy_contact = None
            # Добавляем данные в карту
            map[id]["Дата_рассылки"] = today
            map[id]["Номер_релиза"] = version_number
            map[id]["Наименование_клиента"] = client_name
            map[id]["Основной_контакт"] = main_contact
            map[id]["Копия"] = copy_contact
            today = map[id]["Дата_рассылки"]
            version_number = map[id]["Номер_релиза"]
            client_name = map[id]["Наименование_клиента"]
            main_contact = map[id]["Основной_контакт"]
            copy_contact = map[id]["Копия"]
            result_db.append([today, version_number, client_name, main_contact, copy_contact])
        continue

    # Подключение к базе данных SQLite
    conn = sqlite3.connect('file:/usr/src/app/database.db', uri=True)
    c = conn.cursor()
    # Создаем БД
    c.execute('CREATE TABLE IF NOT EXISTS info (Дата_рассылки date, Номер_релиза number, Наименование_клиента text, Основной_контакт text, Копия text)')
    conn.commit()
    # Наполняем БД
    df = pd.DataFrame(result_db, columns = ["Дата_рассылки", "Номер_релиза", "Наименование_клиента", "Основной_контакт", "Копия"])
    df.to_sql('info', conn, if_exists='append', index = False)