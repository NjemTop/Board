from peewee import *
from model_class import BaseModel, ClientsInfo, Release_info, conn

def get_model_columns(model):
    return {field.column_name: field for field in model._meta.sorted_fields}

# Определяем команду для миграции базы данных
def migrate():
    try:
        # Обход всех моделей
        for model in [ClientsInfo, Release_info]:
            # Проверяем наличие таблицы в БД
            if not model.table_exists():
                # Если таблицы нет, то создаем ее
                with conn:
                    conn.create_tables([model])

            else:
                # Если таблица существует, проверяем ее поля (столбцы)
                current_columns = set(get_model_columns(model).keys())
                expected_columns = set([field.name for field in model._meta.fields])

                # Если поля отсутствуют, добавляем их
                new_columns = expected_columns - current_columns
                for column in new_columns:
                    with conn:
                        conn.execute_sql(f"ALTER TABLE {model._meta.table_name} ADD COLUMN {column} TEXT")

                # Если поля неожиданно присутствуют, удаляем их
                old_columns = current_columns - expected_columns
                for column in old_columns:
                    with conn:
                        conn.execute_sql(f"ALTER TABLE {model._meta.table_name} DROP COLUMN {column}")

        print("Tables created successfully")
    except Exception as error_message:
            print("Error during table creation:", error_message)