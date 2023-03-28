from peewee import *
from model_class import BaseModel, ClientsInfo, Release_info, conn

# Определяем команду для миграции базы данных
def migrate():
    # Обход всех моделей
    for model in [ClientsInfo, Release_info]:
        # Проверяем наличие таблицы в БД
        if not model.table_exists():
            # Если таблицы нет, то создаем ее
            with conn:
                conn.create_table(model)

        else:
            # Если таблица существует, проверяем ее поля (столбцы)
            current_columns = set(model.columns.keys())
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
