import requests
import urllib.parse
import logging
from scripts.NextCloud.check_file import WebDavClient
from logger.log_config import setup_logger, get_abs_log_path

# Указываем настройки логов для нашего файла с классами
bot_error_logger = setup_logger('TeleBot', get_abs_log_path('bot-errors.log'), logging.ERROR)
bot_info_logger = setup_logger('TeleBot', get_abs_log_path('bot-info.log'), logging.INFO)

# Настройка логирования
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')


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
    
    def folder_exists(self, folder_path):
        """
        Проверяет существование папки на сервере Nextcloud.

        :param folder_path: Путь к папке на сервере Nextcloud.
        :return: True, если папка существует, в противном случае False.
        """
        folder_url = self.nextcloud_url + "/remote.php/dav/files/" + self.username + "/" + folder_path.strip("/")
        try:
            response = requests.head(folder_url, auth=(self.username, self.password), timeout=30)
            return response.status_code == 200
        except requests.exceptions.RequestException as error:
            print(f"Ошибка при проверке существования папки: {error}")
            bot_error_logger.error("Ошибка при проверке существования папки: %s", error)
            return False

    def move_folder(self, src_folder_path, dest_folder_path):
        """
        Перемещает папку с одной директории на другую на сервере Nextcloud.

        :param src_folder_path: Путь к исходной папке на сервере Nextcloud.
        :param dest_folder_path: Путь к целевой папке на сервере Nextcloud.
        """
        src_url = self.nextcloud_url + "/remote.php/dav/files/" + self.username + "/" + src_folder_path.strip("/")
        dest_url = self.nextcloud_url + "/remote.php/dav/files/" + self.username + "/" + dest_folder_path.strip("/")

        headers = {
            "Destination": dest_url.encode("utf-8", "ignore").decode("latin-1"),
            "Overwrite": "F",
        }

        try:
            # Проверяем существование родительской директории
            parent_dest_url = self.nextcloud_url + "/remote.php/dav/files/" + self.username + "/" + "/".join(dest_folder_path.split("/")[:-1]).strip("/")
            response = requests.head(parent_dest_url, auth=(self.username, self.password), timeout=30)
            if response.status_code != 200:
                bot_error_logger.error("Родительская директория %s не существует.", parent_dest_url)
                return  # Выход, так как родительская директория не существует

            # Перемещаем папку
            response = requests.request("MOVE", src_url, headers=headers, auth=(self.username, self.password), timeout=30)
            if response.status_code == 201:
                bot_info_logger.info('Папка %s успешно перемещена в %s на Nextcloud.', src_folder_path, dest_folder_path)
            elif response.status_code == 404:
                bot_error_logger.error("Папка %s не найдена на Nextcloud.", src_folder_path)
            elif response.status_code == 412:
                bot_error_logger.error("Папка %s уже существует на Nextcloud.", dest_folder_path)
            else:
                bot_error_logger.error("Ошибка при перемещении папки %s на Nextcloud. Код статуса: %s", src_folder_path, response.status_code)
                bot_error_logger.error("Содержимое ответа сервера: %s", response.text)
        except requests.exceptions.RequestException as error:
            bot_error_logger.error("Ошибка при перемещении папки: %s", error)
            raise Exception(f"Ошибка при перемещении папки: {error}")

    def create_folder(self, folder_path):
        """
        Создает папку на сервере Nextcloud.

        :param folder_path: Путь к создаваемой папке на сервере Nextcloud.
        """
        folder_url = self.nextcloud_url + "/remote.php/dav/files/" + self.username + "/" + folder_path.strip("/")
        headers = {
            "Content-Type": "application/xml; charset=utf-8",
        }
        body = """
            <d:mkcol xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
                <d:set>
                    <d:prop>
                        <d:resourcetype>
                            <d:collection/>
                        </d:resourcetype>
                    </d:prop>
                </d:set>
            </d:mkcol>
        """

        try:
            response = requests.request("MKCOL", folder_url, headers=headers, data=body, auth=(self.username, self.password), timeout=30)
        except requests.exceptions.RequestException as error:
            print(f"Ошибка при создании папки: {error}")
            bot_error_logger.error("Ошибка при создании папки: %s", error)
            raise Exception(f"Ошибка при создании папки: {error}")

        if response.status_code == 201:
            print(f"Папка {folder_path} успешно создана на Nextcloud.")
            bot_info_logger.info('Папка %s успешно создана на Nextcloud.', folder_path)
        elif response.status_code == 405:
            print(f"Папка {folder_path} уже существует на Nextcloud.")
        else:
            print(f"Ошибка при создании папки {folder_path} на Nextcloud. Код статуса: {response.status_code}")
            bot_error_logger.error("Ошибка при создании папки %s на Nextcloud. Код статуса: %s", folder_path, response.status_code)
            print(f"Содержимое ответа сервера: {response.text}")
            bot_error_logger.error("Содержимое ответа сервера: %s", response.text)
