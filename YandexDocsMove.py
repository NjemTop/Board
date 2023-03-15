import requests
from urllib.parse import quote
import os
import tempfile

def download_and_upload_pdf_files(access_token, nextcloud_url, username, password, version, folder_paths):
    """Функция скачивания PDF файлов с Яндекс Диска"""
    # Проходимся циклом по всем папкам с Яндекс.Диска
    for folder_path in folder_paths:
        items = get_yandex_disk_files_list(access_token, folder_path)
        if items is None:
            print(f"Не удалось получить список файлов для папки {folder_path}. Пропуск.")
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
                    response = requests.get(download_url)
                    file.write(response.content)
                
                remote_file_path = f"{nextcloud_folder_path}/{item_name}"
                upload_to_nextcloud(local_file_path, remote_file_path, nextcloud_url, username, password)
                
                os.remove(local_file_path)

def create_nextcloud_folder(folder_path, nextcloud_url, username, password):
    """Функция создания папки с наименованием версии на NextCloud"""
    url = f"{nextcloud_url}/remote.php/dav/files/{username}/{folder_path}"
    response = requests.request("MKCOL", url, auth=(username, password))
    if response.status_code == 201:
        print(f"Папка {folder_path} успешно создана на Nextcloud.")
    elif response.status_code == 405:
        print(f"Папка {folder_path} уже существует на Nextcloud.")
    else:
        print(f"Ошибка при создании папки {folder_path} на Nextcloud: {response.status_code}, {response.text}")

def get_yandex_disk_files_list(access_token, folder_path):
    """Функция парсинга файлов на Яндекс Диске"""
    headers = {
        "Authorization": f"OAuth {access_token}"
    }
    encoded_folder_path = quote(folder_path)
    url = f"https://cloud-api.yandex.net/v1/disk/resources?path={encoded_folder_path}&limit=100"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        response_data = response.json()
        items = response_data['_embedded']['items']
        for item in items:
            item_type = item['type']
            item_name = item['name']
            if item_type == 'dir':
                print(f"Папка: {item_name}")
            elif item_type == 'file':
                print(f"Файл: {item_name}")
                print(f"    Размер: {item['size']} байт")
                print(f"    MIME-тип: {item['mime_type']}")
                print(f"    URL для скачивания: {item['file']}")
            print("\n")
        return items  # Возвращаем список items
    else:
        print(f"Ошибка при получении списка файлов: {response.status_code}, {response.text}")
        return []  # Возвращаем пустой список

def upload_to_nextcloud(local_file_path, remote_file_path, nextcloud_url, username, password):
    """Функция загрузки файлов на NextCloud"""
    url = f"{nextcloud_url}/remote.php/dav/files/{username}/{remote_file_path}"
    with open(local_file_path, "rb") as file:
        response = requests.put(url, data=file, auth=(username, password))
    if response.status_code == 201:
        print(f"Файл {local_file_path} успешно загружен на Nextcloud.")
    else:
        print(f"Ошибка при загрузке файла {local_file_path} на Nextcloud: {response.status_code}, {response.text}")

access_token = "y0_AgAEA7qkB2AWAAlIKgAAAADel0HQaYRTiTBYSu6efA-81KEa9Yxw9eM"
nextcloud_url = "https://cloud.boardmaps.ru"
username = "ncloud"
password = "G6s6kWaZWyOC0oLt"

version = "2.61"
folder_paths = [
    f"/Документация BoardMaps/iPad/{version}/RU",
    f"/Документация BoardMaps/Server/{version}/RU",
    f"/Документация BoardMaps/Server/{version}/RU/USERS",
    f"/Документация BoardMaps/Server/{version}/RU/ADMINISTRATORS",
]

download_and_upload_pdf_files(access_token, nextcloud_url, username, password, version, folder_paths)
