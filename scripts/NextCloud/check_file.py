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
    
    def list_folder(self, folder_path):
        """
        Получает список файлов и папок в заданной папке на NextCloud.

        :param folder_path: Путь к папке на NextCloud.
        :return: Список имен файлов и папок в указанной папке.
        """
        headers = {
            "Depth": "1",  # Глубина просмотра (1 для текущей папки)
            "Content-Type": "application/xml",
        }

        body = """<?xml version="1.0" encoding="utf-8" ?>
            <d:propfind xmlns:d="DAV:">
                <d:prop>
                    <d:resourcetype/>
                </d:prop>
            </d:propfind>
        """

        folder_url = f"{self.url}/remote.php/dav/files/{self.username}/{folder_path.strip('/')}"
        
        try:
            response = requests.request("PROPFIND", folder_url, headers=headers, data=body, auth=(self.username, self.password), timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            print(f"Ошибка при выполнении запроса: {error}")
            raise

        if response.status_code != 207:
            print(f"Ошибка при выполнении PROPFIND-запроса. Код статуса: {response.status_code}, Текст ошибки: {response.text}")
            raise Exception(f"Ошибка при выполнении PROPFIND-запроса. Код статуса: {response.status_code}, Текст ошибки: {response.text}")

        xml_data = ET.fromstring(response.content)


        # Извлекаем имена файлов и папок из ответа
        ns = {"d": "DAV:"}
        items = xml_data.findall(".//d:href", ns)
        folder_items = []

        for item in items:
            item_path = urllib.parse.unquote(item.text)
            # Из всего пути берём только конечную папку, а также удаляем лишние пробелы
            item_name = item_path.split("/")[-2].strip()
            # Исключаем пустые имена
            if item_name:
                folder_items.append(item_name)
                bot_info_logger.info('Папка найдена: "%s"', item_name)

        return folder_items
