from DataBase.model_class import Release_info, ClientsInfo
import sqlite3

# # Создаем таблицу, если она не существует
# Release_info.create_table()

# # Получение всех записей из таблицы
# all_info = Release_info.select()

# # Вывод содержимого таблицы
# for info in all_info:
#     print(info.date, info.release_number, info.client_name, info.main_contact, info.copy)

if __name__ == '__main__':
    # Подключение к базе данных SQLite
    db_filename = './DataBase/database.db'
    conn = sqlite3.connect(f'file:{db_filename}?mode=rw', uri=True)
    
    # Переименовываем таблицу clients_info в BM_info_on_clients
    ClientsInfo.rename_table('clients_info', 'BM_info_on_clients')
