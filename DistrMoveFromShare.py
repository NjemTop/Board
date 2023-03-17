from io import BytesIO
import json
import logging
from smbprotocol.connection import Connection as SMBConnection
from smbprotocol.exceptions import SMBAuthenticationError, SMBResponseException
from urllib.parse import quote
from YandexDocsMove import create_nextcloud_folder, upload_to_nextcloud

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

# Задаем параметры файловой шары
SHARE_IP_ADDRESS = "10.6.75.22"
SHARE_NAME = "data/Releases/[Server]"

def move_distr_file(version):
    """Функция мув дистр на NextCloud"""

    # Создаем соединение с файловой шарой
    try:
        conn = SMBConnection(USERNAME, PASSWORD, "SMBClient")
        conn.connect(SHARE_IP_ADDRESS)
    except SMBAuthenticationError as error:
        print(f"Ошибка аутентификации: {error}")
        distr_move_error_logger.error("Ошибка аутентификации: %s", error)
        return
    except Exception as error:
        print(f"Не удалось установить соединение с файловой шарой: {error}")
        distr_move_error_logger.error("Не удалось установить соединение с файловой шарой:: %s", error)
        return

    # Создаем папку с названием версии на NextCloud
    try:
        create_nextcloud_folder(f"1. Актуальный релиз/Дистрибутив/{version}", NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
    except Exception as error:
        print(f"Не удалось создать папку на NextCloud: {error}")
        distr_move_error_logger.error("Не удалось создать папку на NextCloud: %s", error)
        conn.disconnect()
        return

    # Путь к папке с дистрибутивом на файловой шаре
    distributive_folder = f"\\\\{SHARE_IP_ADDRESS}\\{SHARE_NAME}\\{version}\\Release\\Mainstream" 

    # Ищем файл с расширением .exe в папке с дистрибутивами
    executable_file = None
    try:
        for file_info in conn.list_directory(distributive_folder):
            if file_info.filename.endswith(".exe"):
                executable_file = file_info.filename
                break
    except SMBResponseException as error:
        print(f"Ошибка доступа к файловой шаре: {error}")
    except Exception as error:
        print(f"Произошла ошибка при поиске файла дистрибутива с расширением .exe: {error}")

    if executable_file is not None:
        # Формируем пути к файлу на файловой шаре и на NextCloud
        local_file_path = f"{distributive_folder}\\{executable_file}"
        remote_file_path = f"/1. Актуальный релиз/Дистрибутив/{version}/{executable_file}"
        remote_file_path = quote(remote_file_path, safe="/")  # Кодируем URL-путь

        # Загружаем файл на NextCloud
        try:
            with conn.open_file(conn, local_file_path) as local_file:
                file_content = BytesIO(local_file.read())
                upload_to_nextcloud(file_content, remote_file_path, NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
        except Exception as error:
            print(f"Не удалось прочитать файл на файловой шаре: {error}")
            distr_move_error_logger.error("Не удалось прочитать файл на файловой шаре: %s", error)
    else:
        print("Не удалось найти файл дистрибутива с расширением .exe")

    # Закрываем соединение с файловой шарой
    conn.disconnect()
