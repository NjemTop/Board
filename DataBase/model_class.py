import peewee

# Путь к файлу базы данных
db_filename = 'DataBase/database.db'
# db_filename = './DataBase/database.db'

# Подключение к базе данных SQLite
conn = peewee.SqliteDatabase(f'file:{db_filename}')

# Определяем базовую модель о которой будут наследоваться остальные
class BaseModel(peewee.Model):
    class Meta:
        database = conn  # соединение с базой

# Определяем модель для таблицы "info"
class Info(BaseModel):
    """Класс для таблицы БД info"""
    date = peewee.DateField(column_name='Дата_рассылки')
    release_number = peewee.IntegerField(column_name='Номер_релиза', primary_key=True)
    client_name = peewee.TextField(column_name='Наименование_клиента')
    main_contact = peewee.TextField(column_name='Основной_контакт')
    copy = peewee.TextField(column_name='Копия')

    class Meta:
        table_name = 'info'

class ClientsInfo(BaseModel):
    """Класс для таблицы БД clients_info"""
    client_name = peewee.TextField(column_name='Название клиента', primary_key=True)
    contract_status = peewee.TextField(column_name='Статус по договору')
    service_package = peewee.TextField(column_name='Пакет услуг')
    manager = peewee.TextField(column_name='Менеджер')
    loyalty = peewee.TextField(column_name='Лояльность')
    notes = peewee.TextField(column_name='Примечания')
    server_version = peewee.TextField(column_name='Версия сервера')
    update_date = peewee.DateField(column_name='Дата обновления')

    # Список наименований столбцов
    COLUMN_NAMES = [
        'client_name',
        'contract_status',
        'service_package',
        'manager',
        'loyalty',
        'notes',
        'server_version',
        'update_date'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = ClientsInfo.COLUMN_NAMES
    
    class Meta:
        table_name = 'clients_info'
