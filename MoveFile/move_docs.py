import requests
import urllib.parse
import xml.etree.ElementTree as ET
import logging
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
bot_error_logger = setup_logger('TeleBot', get_abs_log_path('bot-errors.log'), logging.ERROR)
bot_info_logger = setup_logger('TeleBot', get_abs_log_path('bot-info.log'), logging.INFO)

# Настройка логирования
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')

class WebDavClient:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password

    def propfind_request(self, depth=0):
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
        headers = {
            "Depth": str(depth),
            "Content-Type": "application/xml",
        }

        body = """<?xml version="1.0" encoding="utf-8" ?>
            <d:propfind xmlns:d="DAV:">
                <d:prop>
                    <d:resourcetype/>
                </d:prop>
            </d:propfind>
        """

        try:
            response = requests.request("PROPFIND", self.url, headers=headers, data=body, auth=(self.username, self.password), timeout=30)
        except requests.exceptions.RequestException as error:
            print(f"Ошибка при выполнении запроса: {error}")
            bot_error_logger.error("Ошибка при выполнении запроса: %s", error)
            raise Exception(f"Ошибка при выполнении запроса: {error}")

        if response.status_code != 207:
            bot_error_logger.error("Ошибка при выполнении PROPFIND-запроса. Код статуса: %s, Текст ошибки: %s", response.status_code, response.text)
            raise Exception(f"Ошибка при выполнении PROPFIND-запроса. Код статуса: {response.status_code}, Текст ошибки: {response.text}")

        xml_data = ET.fromstring(response.content)

        return xml_data

class NextcloudMover:
    def __init__(self, nextcloud_url, username, password):
        self.nextcloud_url = nextcloud_url
        self.username = username
        self.password = password

    def move_internal_folders(self, src_dir, dest_dir):
        """
        Функция для перемещения внутренних папок из одной директории в другую на Nextcloud.

        :param src_dir: Исходная директория.
        :param dest_dir: Целевая директория.
        :param nextcloud_url: URL-адрес сервера Nextcloud.
        :param username: Имя пользователя Nextcloud.
        :param password: Пароль пользователя Nextcloud.
        """
        ns = {"d": "DAV:"}
        src_url = self.nextcloud_url + "/remote.php/dav/files/" + self.username + "/" + src_dir.strip("/")
        dest_url = self.nextcloud_url + "/remote.php/dav/files/" + self.username + "/" + dest_dir.strip("/")

        # Создание экземпляра класса WebDavClient с аргументами src_url, username и password
        client = WebDavClient(src_url, self.username, self.password)

        # Получение списка элементов исходной директории с использованием метода propfind_request класса WebDavClient
        xml_data = client.propfind_request(depth=1)

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
                response = requests.request("MOVE", item_src_url, headers=headers, auth=(self.username, self.password), timeout=30)
            except requests.exceptions.RequestException as error:
                print(f"Ошибка при выполнении запроса: {error}")
                bot_error_logger.error("Ошибка при выполнении запроса: %s", error)
                raise Exception(f"Ошибка при выполнении запроса: {error}")
        
            if response.status_code == 201:
                print(f"Элемент {src_dir}/{item_name} успешно перемещен в {dest_dir}/{item_name} на Nextcloud.")
                bot_info_logger.info('Элемент %s/%s успешно перемещен в %s/%s на Nextcloud.', src_dir, item_name, dest_dir, item_name)
            elif response.status_code == 404:
                print(f"Элемент {src_dir}/{item_name} не найден на Nextcloud.")
                bot_error_logger.error("Элемент %s/%s не найден на Nextcloud.", src_dir, item_name)
            elif response.status_code == 412:
                print(f"Элемент {dest_dir}/{item_name} уже существует на Nextcloud.")
            else:
                print(f"Ошибка при перемещении элемента {src_dir}/{item_name} на Nextcloud. Код статуса: {response.status_code}")
                bot_error_logger.error("Ошибка при перемещении элемента %s/%s на Nextcloud. Код статуса: %s", src_dir, item_name, response.status_code)
                print(f"Содержимое ответа сервера: {response.text}")
                bot_error_logger.error("Содержимое ответа сервера: %s", response.text)
