import peewee
import uuid

# Путь к файлу базы данных
db_filename = './DataBase/database.db'
# Подключение к базе данных SQLite
conn = peewee.SqliteDatabase(f'file:{db_filename}?encoding=utf-8')

def generate_unique_id():
    """Функция генерации случайного числа для БД"""
    return str(uuid.uuid4())

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
    """Класс для таблицы БД учета клиентов"""
    client_name = peewee.TextField(column_name='Название_клиента', collation='NOCASE')
    contact_status = peewee.BooleanField(column_name='Активность')
    client_info = peewee.AutoField(column_name='Карточка_клиента', primary_key=True)
    service = peewee.TextField(column_name='Обслуживание', default=generate_unique_id)
    technical_information = peewee.TextField(column_name='Тех_информация', default=generate_unique_id)
    integration = peewee.TextField(column_name='Интеграции', default=generate_unique_id)
    documents = peewee.TextField(column_name='Документы', default=generate_unique_id)
    notes = peewee.CharField(column_name='Примечания', null=True)

    # Список наименований столбцов
    COLUMN_NAMES = [
        'client_name',
        'contact_status',
        'client_info',
        'service',
        'technical_information',
        'integration',
        'documents',
        'notes'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = BMInfo_onClient.COLUMN_NAMES
    
    class Meta:
        table_name = 'BM_info_on_clients'

class ClientsCard(BaseModel):
    """Класс для таблицы БД карточек клиентов"""
    client_id = peewee.IntegerField(column_name='Клиент_ID', primary_key=True)
    contacts = peewee.TextField(column_name='Контакты', default=generate_unique_id)
    tech_notes = peewee.TextField(column_name='Технические_заметки', default=generate_unique_id)
    connect_info = peewee.TextField(column_name='Информация_для_подключения', default=generate_unique_id)
    rdp = peewee.TextField(column_name='Удаленный_доступ', default=generate_unique_id)
    tech_account = peewee.TextField(column_name='Технологическая_учетная_запись', default=generate_unique_id)
    bm_servers = peewee.TextField(column_name='Серверы_ВМ', default=generate_unique_id)
    
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
    """Список клиентов (Контакты)"""
    id = peewee.AutoField(column_name='ID', primary_key=True)
    contact_id = peewee.TextField(column_name='ID_Контакта')
    contact_name = peewee.TextField(column_name='ФИО')
    contact_position = peewee.TextField(column_name='Должность', null=True)
    contact_email = peewee.TextField(column_name='Email')
    notification_update = peewee.TextField(column_name='Рассылка_обновление', null=True)
    contact_notes = peewee.TextField(column_name='Примечания', null=True)
    # Список наименований столбцов
    COLUMN_NAMES = [
        'id',
        'contact_id',
        'contact_name',
        'contact_position',
        'contact_email',
        'notification_update',
        'contact_notes'
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = ContactsCard.COLUMN_NAMES

    class Meta:
        table_name = 'contacts_card'

class СonnectInfoCard(BaseModel):
    """Информация для подключения"""
    id = peewee.AutoField(column_name='ID', primary_key=True)
    client_id = peewee.IntegerField(column_name='ID_Клиента')
    contact_info_name = peewee.TextField(column_name='ФИО')
    contact_info_account = peewee.TextField(column_name='Учетная_запись')
    contact_info_password = peewee.TextField(column_name='Пароль')
    # Список наименований столбцов
    COLUMN_NAMES = [
        'id',
        'client_id',
        'contact_info_name',
        'contact_info_account',
        'contact_info_password'
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = СonnectInfoCard.COLUMN_NAMES
    class Meta:
        table_name = 'connect_info_card'

class BMServersCard(BaseModel):
    """Серверы ВМ"""
    bm_server_order = peewee.AutoField(column_name='Порядковый_номер_сервера', primary_key=True)
    bm_servers_id = peewee.IntegerField(column_name='ID_Серверы_ВМ')
    bm_servers_circuit = peewee.TextField(column_name='Контур')
    bm_servers_servers_name = peewee.TextField(column_name='Имя_сервера')
    bm_servers_servers_adress = peewee.TextField(column_name='Адрес_сервера')
    bm_servers_operation_system = peewee.TextField(column_name='Операционная_система', null=True)
    bm_servers_url = peewee.TextField(column_name='URL', null=True)
    bm_servers_role = peewee.TextField(column_name='Роль')
    # Список наименований столбцов
    COLUMN_NAMES = [
        'bm_server_order',
        'bm_servers_id',
        'bm_servers_circuit',
        'bm_servers_servers_name',
        'bm_servers_servers_adress',
        'bm_servers_operation_system',
        'bm_servers_url',
        'bm_servers_role'
    ]   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = BMServersCard.COLUMN_NAMES
    
    class Meta:
        table_name = 'bm_servers_card'
        primary_key = peewee.CompositeKey('bm_servers_id', 'bm_server_order')

class Integration(BaseModel):
    """Класс наименований интеграций в БД"""
    integration_id = peewee.TextField(column_name='ID_интеграций', primary_key=True)
    elasticsearch = peewee.BooleanField(column_name='Elasticsearch', null=True)
    ad = peewee.BooleanField(column_name='AD', null=True)
    adfs = peewee.BooleanField(column_name='ADFS', null=True)
    oauth_2 = peewee.BooleanField(column_name='OAuth_2.0', null=True)
    module_translate = peewee.BooleanField(column_name='Модуль_трансляции', null=True)
    ms_oos = peewee.BooleanField(column_name='MS OOS', null=True)
    exchange = peewee.BooleanField(column_name='Exchange', null=True)
    office_365 = peewee.BooleanField(column_name='Office_365', null=True)
    sfb = peewee.BooleanField(column_name='Skype_For_Business', null=True)
    zoom = peewee.BooleanField(column_name='Zoom', null=True)
    teams = peewee.BooleanField(column_name='Teams', null=True)
    smtp = peewee.BooleanField(column_name='SMTP', null=True)
    cryptopro_dss = peewee.BooleanField(column_name='Cripto_DSS', null=True)
    cryptopro_scp = peewee.BooleanField(column_name='Cripto_CSP', null=True)
    smpp = peewee.BooleanField(column_name='SMPP', null=True)
    limesurvey = peewee.BooleanField(column_name='Анкетирование', null=True)
    # Список наименований столбцов
    COLUMN_NAMES = [
        'integration_id',
        'elasticsearch',
        'ad',
        'adfs',
        'oauth_2',
        'module_translate',
        'ms_oos',
        'exchange',
        'office_365',
        'sfb',
        'zoom',
        'teams',
        'smtp',
        'cryptopro_dss',
        'cryptopro_scp',
        'smpp',
        'limesurvey'
    ]   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = Integration.COLUMN_NAMES
    
    class Meta:
        table_name = 'integration'

class TechAccount(BaseModel):
    """Класс тех. УЗ клиентов в БД (Технологическая учетная запись)"""
    id = peewee.AutoField(column_name='ID', primary_key=True)
    tech_account_id = peewee.TextField(column_name='ID_Тех_уз')
    contact_info_disc = peewee.TextField(column_name='Описание')
    contact_info_account = peewee.TextField(column_name='Учетная_запись')
    contact_info_password = peewee.TextField(column_name='Пароль')
    # Список наименований столбцов
    COLUMN_NAMES = [
        'id',
        'tech_account_id',
        'contact_info_disc',
        'contact_info_account',
        'contact_info_password'
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = TechAccount.COLUMN_NAMES

    class Meta:
        table_name = 'tech_account'

class ConnectionInfo(BaseModel):
    """Класс с информацией о настройке подключении по ВПН (Настройки подключения)"""
    id = peewee.AutoField(primary_key=True)
    client_id = peewee.ForeignKeyField(ClientsCard, column_name='client_id', backref='connection_info', on_delete='CASCADE', null=True)
    file_path = peewee.TextField(column_name='file_path', null=True)
    text = peewee.TextField(column_name='text', null=True)

    COLUMN_NAMES = [
        "id",
        "client_id",
        "file_path",
        "text"
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = ConnectionInfo.COLUMN_NAMES

    class Meta:
        table_name = 'connection_info'

class Servise(BaseModel):
    """Класс 'обслуживание' """
    id = peewee.AutoField(primary_key=True)
    service_id = peewee.ForeignKeyField(BMInfo_onClient, column_name='service', backref='service', on_delete='CASCADE')
    service_pack = peewee.TextField(column_name='Пакет_услуг')
    manager = peewee.TextField(column_name='Менеджер')
    loyal = peewee.TextField(column_name='Лояльность', null=True)
    # Список наименований столбцов
    COLUMN_NAMES = [ 
        'service_id',
        'service_pack',
        'manager',
        'loyal'
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = Servise.COLUMN_NAMES

    class Meta:
        table_name = 'service'       

class TechInformation(BaseModel):
    """класс техническая информация"""
    id = peewee.AutoField(primary_key=True)
    tech_information_id = peewee.ForeignKeyField(BMInfo_onClient, column_name='technical_information', backref='tech_information', on_delete='CASCADE')
    server_version = peewee.TextField(column_name='Версия_сервера')
    update_date = peewee.DateField(column_name='Дата_обновления')
    api = peewee.BooleanField(column_name='API', null=True)
    ipad = peewee.TextField(column_name='iPad', null=True)
    android = peewee.TextField(column_name='Andriod', null=True)
    mdm = peewee.TextField(column_name='MDM', null=True)
    localizable_web = peewee.BooleanField(column_name='Локализация_Web', null=True)
    localizable_ios = peewee.BooleanField(column_name='Локализация_iOS', null=True)
    skins_web = peewee.BooleanField(column_name='Скины_Web', null=True)
    skins_ios = peewee.BooleanField(column_name='Скины_iOS', null=True)
    # Список наименований столбцов
    COLUMN_NAMES = [ 
        'server_version',
        'update_date',
        'api',
        'ipad',
        'android',
        'mdm',
        'localizable_web',
        'localizable_ios',
        'skins_web',
        'skins_ios'
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = TechInformation.COLUMN_NAMES

    class Meta:
        table_name = 'tech_information'
