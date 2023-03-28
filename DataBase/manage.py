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
                current_columns = get_model_columns(model)
                expected_columns = {field.column_name: field for field in model._meta.sorted_fields}

                # Если поля отсутствуют, добавляем их
                new_columns = set(expected_columns.keys()) - set(current_columns.keys())
                for column in new_columns:
                    with conn:
                        conn.execute_sql(f"ALTER TABLE {model._meta.table_name} ADD COLUMN {column} TEXT")

                # Если поля неожиданно присутствуют, удаляем их
                old_columns = set(current_columns.keys()) - set(expected_columns.keys())
                for column in old_columns:
                    with conn:
                        conn.execute_sql(f"ALTER TABLE {model._meta.table_name} DROP COLUMN {column}")

                # Переименовываем столбцы, если имена столбцов в базе данных и классе модели не совпадают
                for column_name, field in expected_columns.items():
                    if column_name in current_columns and field.name != current_columns[column_name].name:
                        with conn:
                            conn.execute_sql(f"ALTER TABLE {model._meta.table_name} RENAME COLUMN {current_columns[column_name].name} TO {field.name}")

        print("Tables created successfully")
    except Exception as error_message:
        print(f"Error: {error_message}")
