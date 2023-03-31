import peewee
import random

# Путь к файлу базы данных
db_filename = './DataBase/database.db'
# Подключение к базе данных SQLite
conn = peewee.SqliteDatabase(f'file:{db_filename}?encoding=utf-8')

def generate_unique_id():
    """Функция генерации случайного числа для БД"""
    # Генерируем уникальный ID. В данном примере используется случайное число.
    return random.randint(1, 10000)

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
    release_number = peewee.FloatField(column_name='Номер_релиза', primary_key=True)
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
    client_name = peewee.TextField(column_name='Название_клиента', collation='NOCASE')
    contact_status = peewee.BooleanField(column_name='Активность')
    client_info = peewee.AutoField(column_name='Карточка_клиента', primary_key=True)
    service = peewee.IntegerField(column_name='Обслуживание', default=generate_unique_id)
    technical_information = peewee.IntegerField(column_name='Тех_информация', default=generate_unique_id)
    integration = peewee.IntegerField(column_name='Интеграции', default=generate_unique_id)
    notes = peewee.CharField(column_name='Примечания', null=True)

    # Список наименований столбцов
    COLUMN_NAMES = [
        'client_name',
        'contact_status',
        'client_info',
        'service',
        'technical_information',
        'integration',
        'notes'
    ]

    # Русский список наименований столбцов
    RU_COLUMN_NAMES = {
    'client_id': 'ID',
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
    client_id = peewee.IntegerField(column_name='Клиент_ID', primary_key=True)
    contacts = peewee.IntegerField(column_name='Контакты', default=generate_unique_id)
    tech_notes = peewee.IntegerField(column_name='Технические_заметки', default=generate_unique_id)
    connect_info = peewee.IntegerField(column_name='Информация_для_подключения', default=generate_unique_id)
    rdp = peewee.IntegerField(column_name='Удаленный_доступ', default=generate_unique_id)
    tech_account = peewee.IntegerField(column_name='Технологическая_учетная_запись', default=generate_unique_id)
    bm_servers = peewee.IntegerField(column_name='Серверы_ВМ', default=generate_unique_id)
    
    # Список наименований столбцов
    COLUMN_NAMES = [
        'client_id',
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





######ID_Технические_заметки и ID_Технологическая_учетная_запись - это просто текст. Нужен разве класс и столбцы?
######ID_Удаленный_доступ - это тоже как текст и картинки. Как сделаем?
class ContactsCard(BaseModel):
    contact_id = peewee.FloatField(column_name='ID_Контакт', primary_key=True)
    contact_name = peewee.TextField(column_name='ФИО')
    contact_position = peewee.TextField(column_name='Должность')
    contact_email = peewee.TextField(column_name='Email')
    contact_notes = peewee.TextField(column_name='Примечания')
    # Список наименований столбцов
    COLUMN_NAMES = [
        'contact_id',
        'contact_name',
        'contact_position',
        'contact_email',
        'contact_notes'
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = ContactsCard.COLUMN_NAMES
    class Meta:
        table_name = 'contact_id'
class СonnectInfoCard(BaseModel):
    connect_info_id = peewee.FloatField(column_name='ID_Информация_для_подключения', primary_key=True)
    contact_info_name = peewee.TextField(column_name='ФИО')
    contact_info_account = peewee.TextField(column_name='Учетная запись')
    contact_info_password = peewee.TextField(column_name='Пароль')
    # Список наименований столбцов
    COLUMN_NAMES = [
        'connect_info',
        'contact_info_name',
        'contact_info_account',
        'contact_info_password'
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = СonnectInfoCard.COLUMN_NAMES
    class Meta:
        table_name = 'connect_info_id'
class BMServersCard(BaseModel):
    bm_servers_id = peewee.FloatField(column_name='ID_Серверы_ВМ', primary_key=True)
    bm_servers_circuit = peewee.TextField(column_name='Контур')
    bm_servers_servers_name = peewee.TextField(column_name='Имя_сервера')
    bm_servers_servers_adress = peewee.TextField(column_name='Адрес_сервера')
    bm_servers_operation_system = peewee.TextField(column_name='Операционная система')
    bm_servers_url = peewee.TextField(column_name='URL')
    bm_servers_software = peewee.TextField(column_name='Программное обеспечение')
    bm_servers_role = peewee.TextField(column_name='Роль')
    # Список наименований столбцов
    COLUMN_NAMES = [
        'bm_servers_id',
        'bm_servers_circuit',
        'bm_servers_servers_name',
        'bm_servers_servers_adress',
        'bm_servers_operation_system',
        'bm_servers_url',
        'bm_servers_software',
        'bm_servers_role'
    ]   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = BMServersCard.COLUMN_NAMES
    
    class Meta:
        table_name = 'bm_servers_id'

