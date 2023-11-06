import os
import tempfile
import shutil
import subprocess
import json
import logging
import requests
from urllib.parse import quote
from scripts.NextCloud.move_file import NextcloudMover
from scripts.YandexDocsMove import create_nextcloud_folder, upload_to_nextcloud
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
bot_error_logger = setup_logger('TeleBot', get_abs_log_path('bot-errors.log'), logging.ERROR)
bot_info_logger = setup_logger('TeleBot', get_abs_log_path('bot-info.log'), logging.INFO)

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

def download_files(share_path, release_path):
    """
    Скачивает файлы с файловой шары во временную папку.

    :param share_path: Путь к файловой шаре.
    :param release_path: Путь к папке с дистрибутивом на файловой шаре.
    """
    # Команда smbclient для подключения к файловой шаре и скачивание файла в текущую директорию
    smbclient_command = f"smbclient {share_path} -U {DOMAIN}/{USERNAME}%{PASSWORD} -c 'prompt; cd {release_path}; mget *.exe'"

    try:
        # Попытка выполнить команду smbclient
        subprocess.run(smbclient_command, shell=True, check=True)
        bot_info_logger.info('Дистрибутив успешно скачен из файловой шары')
    except subprocess.CalledProcessError as cmd_error:
        bot_error_logger.error("Ошибка выполнения smbclient команды: %s", cmd_error)
        raise

def move_files_to_temp_dir(temp_dir):
    """
    Перемещает скачанные файлы во временную папку.

    :param temp_dir: Путь к созданной временной папке.
    :return: Путь к временной папке после перемещения файлов.
    """
    # Список скачанных файлов
    downloaded_files = [file for file in os.listdir() if file.endswith(".exe")]
    if not downloaded_files:
        bot_error_logger.error("Не удалось скачать ни одного файла.")
        return temp_dir

    # Перемещаем скачанные файлы в указанную временную папку
    for file in downloaded_files:
        source_path = os.path.join(os.getcwd(), file)
        destination_path = os.path.join(temp_dir, file)
        shutil.move(source_path, destination_path)
    return temp_dir

def upload_files_to_nextcloud(version, temp_dir):
    """
    Загружает файлы на NextCloud.

    :param version: Номер версии.
    :param temp_dir: Путь к временной папке с скачанными файлами.
    """
    # Создание экземпляра класса NextcloudMover
    nextcloud_mover = NextcloudMover(NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
    
    # Перемещаем содержимое папки на NextCloud
    src_dir = "1. Актуальный релиз/Дистрибутив"
    dest_dir = f"2. Предыдущие релизы/Дистрибутив"
    nextcloud_mover.move_internal_folders(src_dir, dest_dir)

    # Создаем папку с названием версии на NextCloud
    create_nextcloud_folder(f"1. Актуальный релиз/Дистрибутив/{version}", NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
    
    # Формируем пути к файлу на NextCloud
    local_files = os.listdir(temp_dir)
    if not local_files:
        bot_error_logger.error("Временная папка пуста. Нет файлов для загрузки на NextCloud.")
        return

    for file in local_files:
        if file.endswith(".exe"):
            local_file_path = os.path.join(temp_dir, file)  # Путь к файлу в временной папке
            remote_file_path = f"/1. Актуальный релиз/Дистрибутив/{version}/{file}"
            remote_file_path = quote(remote_file_path, safe="/")  # Кодируем URL-путь

            # Загружаем файл на NextCloud
            bot_info_logger.info('Загрузка файла %s на облако', file)
            upload_to_nextcloud(local_file_path, remote_file_path, NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)

            # Удаляем скачанный файл
            try:
                os.remove(local_file_path)
                bot_info_logger.info('Файл успешно удален: %s', local_file_path)
            except FileNotFoundError:
                bot_error_logger.error("Файл не найден: %s", local_file_path)
            except Exception as error:
                bot_error_logger.error("Произошла ошибка при удалении файла: %s", error)

def move_distr_file(version):
    """
    Функция перемещения дистрибутива на NextCloud.

    :param version: Номер версии.
    """
    share_path = f"//{DOMAIN}/data/"
    release_path = f"Releases/[Server]/{version}/Release/Mainstream"
    
    try:
        # Создание временной папки для хранения скачанных файлов
        temp_dir = tempfile.mkdtemp()

        # Скачиваем дистрибутив
        download_files(share_path, release_path)

        # Получаем путь к указанному дистрибутиву и сохраняем его в temp_dir
        temp_dir = move_files_to_temp_dir(temp_dir)

        upload_files_to_nextcloud(version, temp_dir)
    except Exception as error:
        bot_error_logger.error("Произошла ошибка: %s", error)


def move_distr_and_manage_share(version):
    """
    Функция перемещения дистрибутива из файловой шары на облако NextCloud.

    :param version: Номер версии.
    """
    try:
        # Перемещаем дистрибутив на NextCloud
        move_distr_file(version)
        bot_info_logger.info('Перемещение успешно произведено')
    except Exception as error:
        bot_error_logger.error("Произошла ошибка при перемещении дистрибутива: %s", error)
