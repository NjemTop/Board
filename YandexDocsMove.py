import requests
from urllib.parse import quote
import urllib.parse
import os
import tempfile
import xml.etree.ElementTree as ET
from xml.etree import ElementTree as ET
import logging
import requests.exceptions

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
    try:
        # Вызов функции перемещения папки внутри Nextcloud
        src_dir = "1. Актуальный релиз/Документация"
        dest_dir = "2. Предыдущие релизы/Документация"
        move_internal_folders(src_dir, dest_dir, nextcloud_url, username, password)

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

def propfind_request(url, username, password, depth=0):
    """
    Функция выполняет PROPFIND-запрос к серверу WebDAV (Nextcloud).
    PROPFIND-запрос используется для получения свойств и структуры коллекций или ресурсов.

    Args:
        url (str): URL-адрес, к которому отправляется запрос.
        username (str): Имя пользователя для аутентификации на сервере WebDAV.
        password (str): Пароль пользователя для аутентификации на сервере WebDAV.
        depth (int, optional): Глубина просмотра. 0 для текущего ресурса, 1 для ресурса и его непосредственных дочерних элементов. По умолчанию 0.

    Returns:
        xml.etree.ElementTree.Element: Возвращает объект ElementTree с данными, полученными в результате PROPFIND-запроса.

    Raises:
        Exception: Возникает, если код статуса ответа не равен 207.
    """

    # Установка заголовков для запроса
    headers = {
        "Depth": str(depth),
        "Content-Type": "application/xml",
    }

    # Тело запроса на основе XML
    body = """<?xml version="1.0" encoding="utf-8" ?>
        <d:propfind xmlns:d="DAV:">
            <d:prop>
                <d:resourcetype/>
            </d:prop>
        </d:propfind>
    """

    try:
        # Выполнение PROPFIND-запроса с использованием предоставленных аргументов и данных
        response = requests.request("PROPFIND", url, headers=headers, data=body, auth=(username, password), timeout=30)
    except requests.exceptions.RequestException as error:
        print(f"Ошибка при выполнении запроса: {error}")
        YandexDocsMove_error_logger.error("Ошибка при выполнении запроса: %s", error)
        raise Exception(f"Ошибка при выполнении запроса: {error}")

    # Проверка кода статуса ответа
    if response.status_code != 207:
        YandexDocsMove_error_logger.error("Ошибка при выполнении PROPFIND-запроса. Код статуса: %s, Текст ошибки: %s", response.status_code, response.text)
        raise Exception(f"Ошибка при выполнении PROPFIND-запроса. Код статуса: {response.status_code}, Текст ошибки: {response.text}")

    # Преобразование ответа в формате XML в объект ElementTree
    xml_data = ET.fromstring(response.content)

    return xml_data

def move_internal_folders(src_dir, dest_dir, nextcloud_url, username, password):
    """
    Функция для перемещения внутренних папок из одной директории в другую на Nextcloud.

    :param src_dir: Исходная директория.
    :param dest_dir: Целевая директория.
    :param nextcloud_url: URL-адрес сервера Nextcloud.
    :param username: Имя пользователя Nextcloud.
    :param password: Пароль пользователя Nextcloud.
    """
    ns = {"d": "DAV:"}
    src_url = nextcloud_url + "/remote.php/dav/files/" + username + "/" + src_dir.strip("/")
    dest_url = nextcloud_url + "/remote.php/dav/files/" + username + "/" + dest_dir.strip("/")

    # Получение списка элементов исходной директории
    xml_data = propfind_request(src_url, username, password, depth=1)

    # Формирование списка путей элементов исходной директории
    item_paths = [
        e.find("d:href", ns).text for e in xml_data.findall(".//d:response", ns)
    ]

    # Обработка и перемещение внутренних папок исходной директории
    for item_path in item_paths[1:]:
        item_name = urllib.parse.unquote(item_path.split("/")[-2])
        item_src_url = src_url + "/" + urllib.parse.quote(item_name)
        item_dest_url = dest_url + "/" + urllib.parse.quote(item_name)

        headers = {
            "Destination": item_dest_url.encode("utf-8", "ignore").decode("latin-1"),
            "Overwrite": "F",
        }
        try:
            response = requests.request("MOVE", item_src_url, headers=headers, auth=(username, password), timeout=30)
        except requests.exceptions.RequestException as error:
            print(f"Ошибка при выполнении запроса: {error}")
            YandexDocsMove_error_logger.error("Ошибка при выполнении запроса: %s", error)
            raise Exception(f"Ошибка при выполнении запроса: {error}")
    
        if response.status_code == 201:
            print(f"Элемент {src_dir}/{item_name} успешно перемещен в {dest_dir}/{item_name} на Nextcloud.")
            YandexDocsMove_info_logger.info('Элемент %s/%s успешно перемещен в %s/%s на Nextcloud.', src_dir, item_name, dest_dir, item_name)
        elif response.status_code == 404:
            print(f"Элемент {src_dir}/{item_name} не найден на Nextcloud.")
            YandexDocsMove_error_logger.error("Элемент %s/%s не найден на Nextcloud.", src_dir, item_name)
        elif response.status_code == 412:
            print(f"Элемент {dest_dir}/{item_name} уже существует на Nextcloud.")
        else:
            print(f"Ошибка при перемещении элемента {src_dir}/{item_name} на Nextcloud. Код статуса: {response.status_code}")
            YandexDocsMove_error_logger.error("Ошибка при перемещении элемента %s/%s на Nextcloud. Код статуса: %s", src_dir, item_name, response.status_code)
            print(f"Содержимое ответа сервера: {response.text}")
            YandexDocsMove_error_logger.error("Содержимое ответа сервера: %s", response.text)

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

# access_token = ""
# nextcloud_url = "https://cloud.boardmaps.ru"
# username = "ncloud"
# password = ""

# version = "2.61"
# folder_paths = [
#     f"/Документация BoardMaps/iPad/{version}/RU",
#     f"/Документация BoardMaps/Server/{version}/RU",
#     f"/Документация BoardMaps/Server/{version}/RU/USERS",
#     f"/Документация BoardMaps/Server/{version}/RU/ADMINISTRATORS",
# ]

# download_and_upload_pdf_files(access_token, nextcloud_url, username, password, version, folder_paths)
