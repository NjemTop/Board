from peewee import *
from model_class import BaseModel, ClientsInfo, Release_info, conn

# Определяем команду для миграции базы данных
def migrate():
    # Создаем таблицы, если они не существуют
    with conn:
        conn.create_tables([BaseModel, ClientsInfo, Release_info])
