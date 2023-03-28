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

    @property
    def columns(self):
        return {field.column_name: field for field in self._meta.sorted_fields}

    @classmethod
    def rename_table(cls, new_name):
        with cls._meta.database:
            cls._meta.database.execute_sql(f"ALTER TABLE {cls._meta.table_name} RENAME TO {new_name}")
            cls._meta.table_name = new_name

# Определяем модель для таблицы "release_info"
class Release_info(BaseModel):
    """Класс для таблицы БД release_info"""
    date = peewee.DateField(column_name='Дата_рассылки')
    release_number = peewee.IntegerField(column_name='Номер_релиза', primary_key=True)
    client_name = peewee.TextField(column_name='Наименование_клиента')
    main_contact = peewee.TextField(column_name='Основной_контакт')
    copy = peewee.TextField(column_name='Копия')

    # Список наименований столбцов
    COLUMN_NAMES = [
        'date',
        'release_number',
        'client_name',
        'main_contact',
        'copy'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = Release_info.COLUMN_NAMES

    class Meta:
        table_name = 'release_info'

class ClientsInfo(BaseModel):
    """Класс для таблицы БД clients_info"""
    client_name = peewee.TextField(column_name='Название_клиента', primary_key=True)
    contract_status = peewee.TextField(column_name='Статус_по_договору')
    service_package = peewee.TextField(column_name='Пакет_услуг')
    manager = peewee.TextField(column_name='Менеджер')
    loyalty = peewee.TextField(column_name='Лояльность')
    notes = peewee.TextField(column_name='Примечания')
    server_version = peewee.TextField(column_name='Версия_сервера')
    update_date = peewee.DateField(column_name='Дата_обновления')

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
