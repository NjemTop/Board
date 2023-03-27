import peewee
import sqlite3
import shutil

# Имя файла базы данных
db_filename = 'DataBase/app/database.db'

# Подключение к базе данных SQLite
conn = peewee.SqliteDatabase(f'file:{db_filename}')

# Соединяемся с базой данных
connection = sqlite3.connect(f'file:{db_filename}')

# Создание резервной копии базы данных
backup_filename = 'DataBase/app/database_backup.db'
# connection.backup(sqlite3.connect(backup_filename))

# Восстановление базы данных из резервной копии
# shutil.copy(backup_filename, db_filename)

# Определяем базовую модель о которой будут наследоваться остальные
class BaseModel(peewee.Model):
    class Meta:
        database = conn  # соединение с базой

# Определяем модель для таблицы "info"
class Info(BaseModel):
    date = peewee.DateField(column_name='Дата_рассылки')
    release_number = peewee.IntegerField(column_name='Номер_релиза', primary_key=True)
    client_name = peewee.TextField(column_name='Наименование_клиента')
    main_contact = peewee.TextField(column_name='Основной_контакт')
    copy = peewee.TextField(column_name='Копия')

    class Meta:
        table_name = 'info'

# Создаем таблицу, если она не существует
Info.create_table()

# Получение всех записей из таблицы
all_info = Info.select()

# Вывод содержимого таблицы
for info in all_info:
    print(info.date, info.release_number, info.client_name, info.main_contact, info.copy)

# Закрываем соединение с базой данных
conn.close()
