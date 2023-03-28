from peewee import *
from model_class import BaseModel, ClientsInfo, Release_info, conn

def get_model_columns(model):
    return {field.column_name: field for field in model._meta.sorted_fields}

# Определяем команду для миграции базы данных
def migrate():
    try:
        for model in [ClientsInfo, Release_info]:
            if not model.table_exists():
                with conn:
                    conn.create_tables([model])
            else:
                # Получаем столбцы таблицы и модели
                table_columns = conn.get_columns(model._meta.table_name)
                table_column_names = {col.name for col in table_columns}
                model_column_names = set(model().columns.keys())

                if table_column_names != model_column_names:
                    # Создаем новую таблицу с обновленными столбцами
                    new_table_name = model._meta.table_name + '_new'
                    model.rename_table(new_table_name)
                    with conn:
                        conn.create_tables([model])

                    # Копируем данные из старой таблицы в новую
                    common_columns = table_column_names.intersection(model_column_names)
                    common_columns_str = ', '.join(common_columns)
                    query = f"INSERT INTO {model._meta.table_name} ({common_columns_str}) SELECT {common_columns_str} FROM {new_table_name};"
                    with conn:
                        conn.execute_sql(query)

                    # Удаляем старую таблицу
                    with conn:
                        conn.execute_sql(f"DROP TABLE {new_table_name}")

        print("Tables migrated successfully")
    except Exception as e:
        print(f"Error: {e}")

migrate()