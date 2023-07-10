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

class Report_Ticket(BaseModel):
    """Класс для таблицы БД информации с отчётами о тикетах"""
    id = peewee.AutoField(primary_key=True)
    report_date = peewee.DateField(column_name='Дата_отчёта')
    ticket_id = peewee.IntegerField(column_name='Номер_тикета')
    subject = peewee.TextField(column_name='Тема_тикета')
    creation_date = peewee.DateField(column_name='Создан')
    status = peewee.TextField(column_name='Статус')
    client_name = peewee.TextField(column_name='Название_клиента')
    priority = peewee.TextField(column_name='Приоритет')
    assignee_name = peewee.TextField(column_name='Исполнитель')
    updated_at = peewee.DateField(column_name='Дата_обновления')
    last_reply_at = peewee.DateField(column_name='Дата_последнего_ответа_клиенту')
    sla = peewee.BooleanField(column_name='SLA')
    sla_time = peewee.IntegerField(column_name='Общее_время_SLA')
    response_time = peewee.IntegerField(column_name='Среднее_время_ответа')
    cause = peewee.TextField(column_name='Причина_возникновения')
    module_boardmaps = peewee.TextField(column_name='Модуль_BoardMaps')
    staff_message = peewee.IntegerField(column_name='Сообщений_от_саппорта')

    # Список наименований столбцов
    COLUMN_NAMES = [
        'id',
        'report_date',
        'ticket_id',
        'subject',
        'creation_date',
        'status',
        'client_name',
        'priority',
        'assignee_name',
        'updated_at',
        'last_reply_at',
        'sla',
        'sla_time',
        'response_time',
        'cause',
        'module_boardmaps',
        'staff_message'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_names = Report_Ticket.COLUMN_NAMES

    class Meta:
        table_name = 'report_ticket'

