from peewee import *
from model_class import BaseModel, BMInfo_onClient, Release_info, ClientsCard, ContactsCard, СonnectInfoCard, BMServersCard, Integration, TechAccount, conn

def get_model_columns(model):
    return {field.column_name: field for field in model._meta.sorted_fields}

def migrate():
    try:
        for model in [BMInfo_onClient, Release_info, ClientsCard, ContactsCard, СonnectInfoCard, BMServersCard, Integration, TechAccount]:
            if not model.table_exists():
                with conn:
                    conn.create_tables([model])
                    print(f"Таблица {model} создана")
            else:
                # Получаем столбцы таблицы и модели
                table_columns = conn.get_columns(model._meta.table_name)
                table_column_names = {col.name for col in table_columns}
                model_column_names = set(model().columns.keys())

                if table_column_names != model_column_names:
                    print(f"Начат процесс миграции строк таблицы {model} начат")
                    # Создаем новую таблицу с обновленными столбцами
                    new_table_name = model._meta.table_name + '_new'

                    # Создаем новый класс для временной таблицы
                    class TempModel(model):
                        class Meta:
                            table_name = new_table_name

                    with conn:
                        conn.create_tables([TempModel])
                        print(f"Новая таблица {model} создана")

                    # Копируем данные из старой таблицы в новую
                    common_columns = table_column_names.intersection(model_column_names)
                    common_columns_str = ', '.join(common_columns)
                    print(f"Новые столбцы: {model_column_names}, для таблицы {model}.")
                    query = f"INSERT INTO {new_table_name} ({common_columns_str}) SELECT {common_columns_str} FROM {model._meta.table_name};"
                    with conn:
                        conn.execute_sql(query)
                        print(f"Копирование таблицы {model} завершено")

                    # Удаляем старую таблицу
                    with conn:
                        conn.execute_sql(f"DROP TABLE {model._meta.table_name}")
                        print(f"Удаление старой таблицы {model} завершено")

                    # Переименовываем новую таблицу
                    with conn:
                        conn.execute_sql(f"ALTER TABLE {new_table_name} RENAME TO {model._meta.table_name}")
                        print(f"Переименование таблицы {model} завершено")

        print("Tables migrated successfully")
    except Exception as e:
        print(f"Error: {e}")

print("Starting migration...", flush=True)
migrate()
print("Migration completed.", flush=True)
