from DataBase.model_class import Info

# Создаем таблицу, если она не существует
Info.create_table()

# Получение всех записей из таблицы
all_info = Info.select()

# Вывод содержимого таблицы
for info in all_info:
    print(info.date, info.release_number, info.client_name, info.main_contact, info.copy)
