import os
import subprocess
import json
from pathlib import Path
import logging
from urllib.parse import quote
from YandexDocsMove import create_nextcloud_folder, upload_to_nextcloud, move_internal_folders

# Настройка логирования
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')

# Создание объекта логгера для ошибок и критических событий
distr_move_error_logger = logging.getLogger('DistrMoveError')
distr_move_error_logger.setLevel(logging.ERROR)
distr_move_error_handler = logging.FileHandler('./logs/distr_move-error.log')
distr_move_error_handler.setLevel(logging.ERROR)
distr_move_error_handler.setFormatter(formatter)
distr_move_error_logger.addHandler(distr_move_error_handler)

# Создание объекта логгера для информационных сообщений
distr_move_info_logger = logging.getLogger('DistrMoveInfo')
distr_move_info_logger.setLevel(logging.INFO)
distr_move_info_handler = logging.FileHandler('./logs/distr_move-info.log')
distr_move_info_handler.setLevel(logging.INFO)
distr_move_info_handler.setFormatter(formatter)
distr_move_info_logger.addHandler(distr_move_info_handler)

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"
# Открываем файл и загружаем данные
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    data = json.load(file)

# Получаем учётные данные из конфиг-файла
USERNAME = data["FILE_SHARE"]["USERNAME"]
PASSWORD = data["FILE_SHARE"]["PASSWORD"]
DOMAIN = data["FILE_SHARE"]["DOMAIN"]

# Получаем данные для доступа к NextCloud из конфиг-файла
NEXTCLOUD_URL = data["NEXT_CLOUD"]["URL"]
NEXTCLOUD_USERNAME = data["NEXT_CLOUD"]["USER"]
NEXTCLOUD_PASSWORD = data["NEXT_CLOUD"]["PASSWORD"]

def move_distr_file(version):
    """Функция мув дистр на NextCloud"""
    # Создаем папку с названием версии на NextCloud
    create_nextcloud_folder(f"1. Актуальный релиз/Дистрибутив/{version}", NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
    # Путь к папке с дистрибутивом на файловой шаре
    distributive_folder = f"/windows_share/{version}/Release/Mainstream"
    # Ищем файл с расширением .exe в папке с дистрибутивами
    executable_file = None
    try:
        for file in os.listdir(distributive_folder):
            if file.endswith(".exe"):
                executable_file = file
                break
    except FileNotFoundError:
        print(f"Не удалось найти папку {distributive_folder}. Проверьте доступность файловой шары.")
        distr_move_error_logger.error("Не удалось найти папку %s. Проверьте доступность файловой шары.", distributive_folder)
    except OSError as error:
        print(f"Произошла ошибка при чтении папки {distributive_folder}: {error}")
        distr_move_error_logger.error("Произошла ошибка при чтении папки %s. Ошибка: %s", distributive_folder, error)
    except Exception as error:
        print(f"Произошла ошибка при поиске файла дистрибутива с расширением .exe: {error}")
        distr_move_error_logger.error("Произошла ошибка при поиске файла дистрибутива с расширением .exe: %s", error)
    if executable_file is not None:
        # Формируем пути к файлу на файловой шаре и на NextCloud
        local_file_path = os.path.join(distributive_folder, executable_file)
        remote_file_path = f"/1. Актуальный релиз/Дистрибутив/{version}/{executable_file}"
        remote_file_path = quote(remote_file_path, safe="/")  # Кодируем URL-путь
        # Загружаем файл на NextCloud
        upload_to_nextcloud(local_file_path, remote_file_path, NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
    else:
        print("Не удалось найти файл дистрибутива с расширением .exe")
        distr_move_error_logger.error("Не удалось найти файл дистрибутива с расширением .exe")

def move_distr_and_manage_share(version):
    try:
        # Перемещаем содержимое папки на NextCloud
        src_dir = "1. Актуальный релиз/Дистрибутив"
        dest_dir = f"2. Предыдущие релизы/Дистрибутив"
        move_internal_folders(src_dir, dest_dir, NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
        # Перемещаем дистрибутив на NextCloud
        move_distr_file(version)
    except Exception as error:
        print(f"Произошла ошибка при перемещении дистрибутива: {error}")
        distr_move_error_logger.error("Произошла ошибка при перемещении дистрибутива: %s", error)
    finally:
        print("Перемещение успешно произведенно")
        distr_move_info_logger.info('Перемещение успешно произведенно')
