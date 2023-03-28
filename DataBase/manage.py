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

                # Создаем список переименованных столбцов
                renamed_columns = []
                for column_name, field in expected_columns.items():
                    if column_name in current_columns and field.name != current_columns[column_name].name:
                        renamed_columns.append((current_columns[column_name].name, field.name))

                if renamed_columns:
                    # Создаем новую таблицу с новыми именами столбцов
                    temp_table_name = f"{model._meta.table_name}_temp"
                    with conn:
                        conn.create_tables([model], safe=False, table_name=temp_table_name)

                    # Копируем данные из старой таблицы в новую
                    old_columns = [old_name for old_name, _ in renamed_columns]
                    new_columns = [new_name for _, new_name in renamed_columns]
                    old_columns_str = ", ".join(old_columns)
                    new_columns_str = ", ".join(new_columns)
                    with conn:
                        conn.execute_sql(f"INSERT INTO {temp_table_name} ({new_columns_str}) SELECT {old_columns_str} FROM {model._meta.table_name}")

                    # Удаляем старую таблицу и переименовываем новую
                    with conn:
                        conn.execute_sql(f"DROP TABLE {model._meta.table_name}")
                        conn.execute_sql(f"ALTER TABLE {temp_table_name} RENAME TO {model._meta.table_name}")

        print("Tables created successfully")
    except Exception as e:
        print(f"Error: {e}")
