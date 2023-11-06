import os
import json
import requests
import subprocess
import logging
import tempfile
import shutil
from urllib.parse import quote
from scripts.NextCloud.check_file import WebDavClient
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

# Получаем учетные данные из конфиг-файла
USERNAME = data["FILE_SHARE"]["USERNAME"]
PASSWORD = data["FILE_SHARE"]["PASSWORD"]
DOMAIN = data["FILE_SHARE"]["DOMAIN"]

# Получаем данные для доступа к NextCloud из конфиг-файла
NEXTCLOUD_URL = data["NEXT_CLOUD"]["URL"]
NEXTCLOUD_USERNAME = data["NEXT_CLOUD"]["USER"]
NEXTCLOUD_PASSWORD = data["NEXT_CLOUD"]["PASSWORD"]
CREG_USERNAME = data['CREG']['USERNAME']
CREG_PASSWORD = data['CREG']['PASSWORD']

# Эндпоинт для получения списка клиентов
CREG_API_ENDPOINT = "http://creg.boardmaps.ru/api/clients/?skins_ios=True"

# Создание экземпляра класса WebDavClient
webdav_client = WebDavClient(NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)

# Создание экземпляра класса NextcloudMover
nextcloud_mover = NextcloudMover(NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)

def get_clients_list(username, password):
    """
    Получает список клиентов с API.

    :param username: Имя пользователя для аутентификации.
    :param password: Пароль для аутентификации.
    :return: Список клиентов в формате JSON.
    """
    try:
        response = requests.get(CREG_API_ENDPOINT, auth=(username, password))
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        bot_error_logger.error("Ошибка при получении списка клиентов: %s", str(e))
        return []


# Функция для скачивания скинов клиента
def download_files(share_path, release_path, skin_filename):
    """
    Скачивает файл с заданным именем из файловой шары во временную папку.

    :param share_path: Путь к файловой шаре.
    :param release_path: Путь к папке с дистрибутивом на файловой шаре.
    :param skin_filename: Имя файла скина для скачивания.
    """
    # Создайте временную папку для скачивания файлов
    temp_dir = tempfile.mkdtemp()

    # Команда smbclient для подключения к файловой шаре и скачивание файла с заданным именем
    smbclient_command = f"smbclient {share_path} -U {DOMAIN}/{USERNAME}%{PASSWORD} -c 'prompt; cd {release_path}; get {skin_filename}'"

    try:
        # Попытка выполнить команду smbclient
        subprocess.run(smbclient_command, shell=True, check=True, cwd=temp_dir)
        bot_info_logger.info('Файл %s успешно скачан из файловой шары в временную папку: %s', skin_filename, temp_dir)
    except subprocess.CalledProcessError as cmd_error:
        bot_error_logger.error("Ошибка выполнения smbclient команды: %s", cmd_error)
        raise

    return temp_dir


# Функция для перемещения старой папки "BoardMaps" в "Старые версии"
def move_old_boardmaps_folder(client_name):
    """
    Перемещает старую папку "BoardMaps" в директорию "{client_name}/1. Кастомизация/Старые версии/".

    :param client_name: Имя клиента.
    """
    try:
        # Путь к текущей директории клиента
        client_directory = f"{client_name}/1. Кастомизация/"

        # Путь к целевой папке "Старые версии"
        old_versions_path = f"{client_name}/1. Кастомизация/Старые версии/"

        # Проверяем, существует ли папка "Старые версии". Если нет, создаем ее.
        if not nextcloud_mover.folder_exists(old_versions_path):
            webdav_client.create_folder(old_versions_path)

        # Получаем список папок в текущей директории клиента
        folders = webdav_client.list_folder(client_directory)

        # Ищем папку "BoardMaps" в списке папок
        for folder in folders:
            if folder.startswith("BoardMaps"):
                old_boardmaps_path = f"{client_directory}{folder}"
                bot_info_logger.info('Путь к папки для перемещения сформирован: "%s"', old_boardmaps_path)

                # Формируем полный путь к перемещаемой папке в целевой директории
                destination_path = f"{old_versions_path}{folder}"

                # Муваем папку в "Старые версии"
                nextcloud_mover.move_folder(old_boardmaps_path, destination_path)

                bot_info_logger.info('Старая папка "BoardMaps" успешно перемещена в директорию "%s"', old_versions_path)
                break

    except Exception as error:
        bot_error_logger.error("Произошла ошибка при перемещении старой папки 'BoardMaps': %s", error)

# Основная функция для перемещения скинов клиентов
def move_skins_and_manage_share(version):
    """
    Функция для перемещения скинов клиентов из файловой шары в NextCloud.

    :param version: Номер версии.
    """
    try:
        # Получаем список клиентов
        clients_list = get_clients_list(CREG_USERNAME, CREG_PASSWORD)

        # Обрабатываем скины для каждого клиента
        for client in clients_list:
            client_name = client.get("short_name")
            if not client_name:
                continue  # Пропускаем клиентов без имени

            # Скачиваем скин для текущего клиента
            share_path = f"//{DOMAIN}/data/"
            release_path = f"Releases/[iPad-skins]/{version}"
            skin_filename = f"{client_name}.zip"
            temp_dir = download_files(share_path, release_path, skin_filename)

            # Перемещаем старую папку "BoardMaps" в "Старые версии"
            move_old_boardmaps_folder(client_name)

            # Создаем папку на NextCloud для клиента
            client_folder_path = f"{client_name}/1. Кастомизация/BoardMaps {version}"
            nextcloud_mover.create_folder(client_folder_path)

            # Перемещаем скин клиента в папку на NextCloud
            local_skin_path = os.path.join(temp_dir, skin_filename)
            remote_skin_path = f"{client_folder_path}/{skin_filename}"
            remote_skin_path = quote(remote_skin_path, safe="/")

            # Загружаем скин на NextCloud
            upload_to_nextcloud(local_skin_path, remote_skin_path, NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)

            # Удаляем скачанный скин
            try:
                os.remove(local_skin_path)
            except FileNotFoundError:
                bot_error_logger.error("Скин не найден: %s", local_skin_path)
            except Exception as error:
                bot_error_logger.error("Произошла ошибка при удалении скина: %s", error)

        bot_info_logger.info('Перемещение скинов успешно произведено')
    except Exception as error:
        bot_error_logger.error("Произошла ошибка при перемещении скинов: %s", error)
