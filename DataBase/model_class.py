import peewee

# Путь к файлу базы данных
db_filename = './DataBase/database.db'
# db_filename = './DataBase/database.db'

# Подключение к базе данных SQLite
conn = peewee.SqliteDatabase(f'file:{db_filename}', charset='utf8')

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
    date = peewee.DateField(column_name='Дата_рассылки')
    release_number = peewee.IntegerField(column_name='Номер_релиза', primary_key=True)
    client_name = peewee.TextField(column_name='Наименование_клиента')
    main_contact = peewee.TextField(column_name='Основной_контакт')
    copy = peewee.TextField(column_name='Копия')

    # Список наименований столбцов
    COLUMN_NAMES = [
        'rate',
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

class BMInfo_onClient(BaseModel):
    """Класс для таблицы БД учёта клиентов"""
    client_name = peewee.TextField(column_name='Название_клиента', primary_key=True)
    contact_status = peewee.BooleanField(column_name='Активность')
    client_info = peewee.IntegerField(column_name='Карточка_клиента')
    service = peewee.IntegerField(column_name='Обслуживание')
    technical_information = peewee.IntegerField(column_name='Техническая_информация')
    integration = peewee.IntegerField(column_name='Интеграции')
    notes = peewee.TextField(column_name='Примечания')

    # Список наименований столбцов
    COLUMN_NAMES = [
        'client_name',
        'contact_status',
        'client_info',
        'client_info',
        'technical_information',
        'integration',
        'notes'
    ]

    # Русский список наименований столбцов
    RU_COLUMN_NAMES = {
    'client_name': 'Название клиента',
    'contact_status': 'Активность',
    'client_info': 'Карточка клиента',
    'service': 'Обслуживание',
    'technical_information': 'Техническая информация',
    'integration': 'Интеграции',
    'notes': 'Примечания'
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = BMInfo_onClient.COLUMN_NAMES
    
    class Meta:
        table_name = 'BM_info_on_clients'

class ClientsCard(BaseModel):
    """Класс для таблицы БД карточек клиентов"""
    clients_id = peewee.IntegerField(column_name='Клиент_ID', primary_key=True)
    contacts = peewee.IntegerField(column_name='Контакты')
    tech_notes = peewee.IntegerField(column_name='Технические_заметки')
    connect_info = peewee.IntegerField(column_name='Информация_для_подключения')
    rdp = peewee.IntegerField(column_name='Удаленный_доступ')
    tech_account = peewee.IntegerField(column_name='Технологическая_учетная_запись')
    bm_servers = peewee.IntegerField(column_name='Серверы_ВМ')
    
    # Список наименований столбцов
    COLUMN_NAMES = [
        'clients_id',
        'contacts',
        'tech_notes',
        'connect_info',
        'rdp',
        'tech_account',
        'bm_servers'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = ClientsCard.COLUMN_NAMES
    
    class Meta:
        table_name = 'clients_card'