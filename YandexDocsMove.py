import requests
from urllib.parse import quote
import urllib.parse
import os
import tempfile
import xml.etree.ElementTree as ET
from xml.etree import ElementTree as ET
import logging
import requests.exceptions
from MoveFile.move_docs import NextcloudMover, WebDavClient

# Настройка логирования
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')

# Создание объекта логгера для ошибок и критических событий
YandexDocsMove_error_logger = logging.getLogger('YandexDocsMoveError')
YandexDocsMove_error_logger.setLevel(logging.ERROR)
YandexDocsMove_error_handler = logging.FileHandler('./logs/yandex_docs_move-error.log')
YandexDocsMove_error_handler.setLevel(logging.ERROR)
YandexDocsMove_error_handler.setFormatter(formatter)
YandexDocsMove_error_logger.addHandler(YandexDocsMove_error_handler)

# Создание объекта логгера для информационных сообщений
YandexDocsMove_info_logger = logging.getLogger('YandexDocsMoveInfo')
YandexDocsMove_info_logger.setLevel(logging.INFO)
YandexDocsMove_info_handler = logging.FileHandler('./logs/yandex_docs_move-info.log')
YandexDocsMove_info_handler.setLevel(logging.INFO)
YandexDocsMove_info_handler.setFormatter(formatter)
YandexDocsMove_info_logger.addHandler(YandexDocsMove_info_handler)

def download_and_upload_pdf_files(access_token, nextcloud_url, username, password, version, folder_paths):
    """
    Функция для скачивания PDF-файлов с Яндекс.Диска и загрузки их на Nextcloud.

    Args:
        access_token (str): Токен доступа Яндекс.Диска.
        nextcloud_url (str): URL-адрес Nextcloud.
        username (str): Имя пользователя Nextcloud.
        password (str): Пароль пользователя Nextcloud.
        version (str): Версия документации для использования в имени папки.
        folder_paths (List[str]): Список путей к папкам на Яндекс.Диске, которые нужно обработать.

    """
    # Создание экземпляра класса NextcloudMover
    nextcloud_mover = NextcloudMover(nextcloud_url, username, password)
    try:
        
        # Вызов функции перемещения папки внутри Nextcloud
        src_dir = "1. Актуальный релиз/Документация"
        dest_dir = "2. Предыдущие релизы/Документация"
        # move_internal_folders(src_dir, dest_dir, nextcloud_url, username, password)
        nextcloud_mover.move_internal_folders(src_dir, dest_dir)
        # Проходимся циклом по всем папкам с Яндекс.Диска
        for folder_path in folder_paths:
            items = get_yandex_disk_files_list(access_token, folder_path)
            if items is None:
                print(f"Не удалось получить список файлов для папки {folder_path}. Пропуск.")
                YandexDocsMove_error_logger.error("Не удалось получить список файлов для папки %s. Пропуск.", folder_path)
                continue

            # Создание папки на Nextcloud
            nextcloud_folder_path = f"1. Актуальный релиз/Документация/{version}"
            create_nextcloud_folder(nextcloud_folder_path, nextcloud_url, username, password)

            for item in items:
                item_type = item['type']
                item_name = item['name']

                # Загрузка файла с Яндекс.Диска
                if item_type == 'file' and item_name.endswith(".pdf") or item_name.endswith(".txt"):
                    if 'USERS' in folder_path and not item_name.startswith(('U10.0.0', 'U20.0.0')):
                        continue
                    download_url = item['file']
                    local_file_path = os.path.join(tempfile.gettempdir(), item_name)
                    with open(local_file_path, "wb") as file:
                        response = requests.get(download_url, timeout=30)
                        file.write(response.content)

                    remote_file_path = f"{nextcloud_folder_path}/{item_name}"
                    upload_to_nextcloud(local_file_path, remote_file_path, nextcloud_url, username, password)
                    os.remove(local_file_path)
    except requests.exceptions.RequestException as error:
        print(f"Произошла ошибка: {error}")
        YandexDocsMove_error_logger.error("Произошла ошибка: %s", error)
    except IOError as error:
        print(f"Ошибка ввода-вывода: {error}")
        YandexDocsMove_error_logger.error("Ошибка ввода-вывода: %s", error)

def create_nextcloud_folder(folder_path, nextcloud_url, username, password):
    """
    Функция для создания папки на Nextcloud.

    Args:
        folder_path (str): Путь к папке, которую нужно создать на Nextcloud.
        nextcloud_url (str): URL-адрес сервера Nextcloud.
        username (str): Имя пользователя для аутентификации на сервере Nextcloud.
        password (str): Пароль для аутентификации на сервере Nextcloud.

    """
    try:
        url = f"{nextcloud_url}/remote.php/dav/files/{username}/{folder_path}"
        response = requests.request("MKCOL", url, auth=(username, password), timeout=30)
        if response.status_code == 201:
            print(f"Папка {folder_path} успешно создана на Nextcloud.")
            YandexDocsMove_info_logger.info('Папка %s успешно создана на Nextcloud.', folder_path)
        elif response.status_code == 405:
            print(f"Папка {folder_path} уже существует на Nextcloud.")
        else:
            print(f"Ошибка при создании папки {folder_path} на Nextcloud. Код статуса: {response.status_code}, Текст ошибки: {response.text}")
            YandexDocsMove_error_logger.error("Ошибка при создании папки %s на Nextcloud. Код статуса: %s, Текст ошибки: %s", folder_path, response.status_code, response.text)
    except requests.exceptions.RequestException as error:
        print(f"Произошла ошибка: {error}")
        YandexDocsMove_error_logger.error("Произошла ошибка: %s", error)
    except IOError as error:
        print(f"Ошибка ввода-вывода: {error}")
        YandexDocsMove_error_logger.error("Ошибка ввода-вывода: %s", error)

def get_yandex_disk_files_list(access_token, folder_path):
    """
    Функция для получения списка файлов и папок, находящихся на Яндекс.Диске в указанной папке.

    Args:
        access_token (str): Токен доступа Яндекс.Диска.
        folder_path (str): Путь к папке на Яндекс.Диске, для которой нужно получить список файлов.

    Returns:
        list: Список элементов (файлов и папок) в указанной папке на Яндекс.Диске. 
              В случае ошибки возвращает пустой список.
    """
    headers = {
        "Authorization": f"OAuth {access_token}"
    }
    encoded_folder_path = quote(folder_path)
    url = f"https://cloud-api.yandex.net/v1/disk/resources?path={encoded_folder_path}&limit=100"
    try:
        response = requests.get(url, headers=headers, timeout=30)
    except requests.exceptions.RequestException as error:
        print(f"Ошибка при выполнении запроса: {error}")
        YandexDocsMove_error_logger.error("Ошибка при выполнении запроса: %s", error)
        return []  # Возвращаем пустой список
    
    if response.status_code == 200:
        response_data = response.json()
        items = response_data['_embedded']['items']
        # Возвращаем список items
        return items
    else:
        print(f"Ошибка при получении списка файлов: {response.status_code}, {response.text}")
        YandexDocsMove_error_logger.error("Ошибка при получении списка файлов. Код статуса: %s, Текст ошибки: %s", response.status_code, response.text)
        return []  # Возвращаем пустой список

def upload_to_nextcloud(local_file_path, remote_file_path, nextcloud_url, username, password):
    """
    Функция для загрузки файлов на Nextcloud.

    Args:
        local_file_path (str): Путь к локальному файлу, который нужно загрузить на Nextcloud.
        remote_file_path (str): Путь к файлу на сервере Nextcloud, куда файл будет загружен.
        nextcloud_url (str): URL-адрес сервера Nextcloud.
        username (str): Имя пользователя для аутентификации на сервере Nextcloud.
        password (str): Пароль для аутентификации на сервере Nextcloud.

    """
    url = f"{nextcloud_url}/remote.php/dav/files/{username}/{remote_file_path}"
    with open(local_file_path, "rb") as file:
        response = requests.put(url, data=file, auth=(username, password), timeout=30)
    if response.status_code == 201:
        print(f"Файл {local_file_path} успешно загружен на Nextcloud.")
        YandexDocsMove_info_logger.info("Файл %s успешно загружен на Nextcloud.", local_file_path)
    else:
        print(f"Ошибка при загрузке файла {local_file_path} на Nextcloud: {response.status_code}, {response.text}")
        YandexDocsMove_error_logger.error("Ошибка при загрузке файла %s на Nextcloud. Код статуса: %s, Текст ошибки: %s", local_file_path, response.status_code, response.text)

# access_token = "y0_AgAEA7qkB2AWAAlIKgAAAADel0HQaYRTiTBYSu6efA-81KEa9Yxw9eM"
# nextcloud_url = "https://cloud.boardmaps.ru"
# username = "ncloud"
# password = "G6s6kWaZWyOC0oLt"

# version = "2.61"
# folder_paths = [
#     f"/Документация BoardMaps/iPad/{version}/RU",
#     f"/Документация BoardMaps/Server/{version}/RU",
#     f"/Документация BoardMaps/Server/{version}/RU/USERS",
#     f"/Документация BoardMaps/Server/{version}/RU/ADMINISTRATORS",
# ]

# download_and_upload_pdf_files(access_token, nextcloud_url, username, password, version, folder_paths)
