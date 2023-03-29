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
    def rename_table(cls, old_name, new_name):
        with cls._meta.database:
            cls._meta.database.execute_sql(f"ALTER TABLE {old_name} RENAME TO {new_name}")

# Определяем модель для таблицы "release_info"
class Release_info(BaseModel):
    """Класс для таблицы БД информации о релизе"""
    Date = peewee.DateField(column_name='Дата_рассылки')
    Release_number = peewee.IntegerField(column_name='Номер_релиза', primary_key=True)
    Client_name = peewee.TextField(column_name='Наименование_клиента')
    Main_contact = peewee.TextField(column_name='Основной_контакт')
    Copy = peewee.TextField(column_name='Копия')

    # Список наименований столбцов
    COLUMN_NAMES = [
        'Date',
        'Release_number',
        'Client_name',
        'Main_contact',
        'Copy'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = Release_info.COLUMN_NAMES

    class Meta:
        table_name = 'release_info'

class BMInfo_onClient(BaseModel):
    """Класс для таблицы БД учёта клиентов"""
    client_name = peewee.TextField(column_name='Название_клиента', primary_key=True)
    Contact_status = peewee.BooleanField(column_name='Активность')
    Client_info = peewee.IntegerField(column_name='Карточка_клиента')
    Service = peewee.IntegerField(column_name='Обслуживание')
    Technical_information = peewee.IntegerField(column_name='Техническая_информация')
    Integration = peewee.IntegerField(column_name='Интеграции')
    Notes = peewee.TextField(column_name='Примечания')

    # Список наименований столбцов
    COLUMN_NAMES = [
        'client_name',
        'Contact_status',
        'client_info',
        'Client_info',
        'Rechnical_information',
        'Integration',
        'Notes'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = BMInfo_onClient.COLUMN_NAMES
    
    class Meta:
        table_name = 'BM_info_on_clients'

class ClientsCard(BaseModel):
    """Класс для таблицы БД карточек клиентов"""
    Clients_id = peewee.IntegerField(column_name='Клиент_ID', primary_key=True)
    Contacts = peewee.IntegerField(column_name='Контакты')
    Tech_notes = peewee.IntegerField(column_name='Технические_заметки')
    Connect_info = peewee.IntegerField(column_name='Информация_для_подключения')
    Rdp = peewee.IntegerField(column_name='Удаленный_доступ')
    Tech_account = peewee.IntegerField(column_name='Технологическая_учетная_запись')
    Bm_servers = peewee.IntegerField(column_name='Серверы_ВМ')
    
    # Список наименований столбцов
    COLUMN_NAMES = [
        'Clients_id',
        'Contacts',
        'Tech_notes',
        'Connect_info',
        'Rdp',
        'Tech_account',
        'Bm_servers'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = ClientsCard.COLUMN_NAMES
    
    class Meta:
        table_name = 'clients_card'