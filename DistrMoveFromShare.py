import os
import subprocess
import json
from pathlib import Path
import logging
from urllib.parse import quote
from YandexDocsMove import create_nextcloud_folder, upload_to_nextcloud

# Настройка логирования
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')

# Создание объекта логгера для ошибок и критических событий
distr_move_error_logger = logging.getLogger('DistrMoveError')
distr_move_error_logger.setLevel(logging.ERROR)
distr_move_error_handler = logging.FileHandler('distr_move-error.log')
distr_move_error_handler.setLevel(logging.ERROR)
distr_move_error_handler.setFormatter(formatter)
distr_move_error_logger.addHandler(distr_move_error_handler)

# Создание объекта логгера для информационных сообщений
distr_move_info_logger = logging.getLogger('DistrMoveInfo')
distr_move_info_logger.setLevel(logging.INFO)
distr_move_info_handler = logging.FileHandler('distr_move-info.log')
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
share_path = r"//corp.boardmaps.com/data/Releases/[Server]"
mount_point = "/mnt/windows_share"

def mount_share(share_path, mount_point):
    # Монтируем файловую шару
    mount_cmd = f"mount -t cifs {share_path} {mount_point} -o username={USERNAME},password={PASSWORD},domain={DOMAIN}"
    mount_result = subprocess.run(mount_cmd, shell=True, stderr=subprocess.PIPE, text=True, check=False, timeout=30)
    # Проверяем, получилось или нет
    if mount_result.returncode != 0:
        print(f"Не удалось смонтировать файловую шару. Код возврата: {mount_result.returncode}. Ошибка: {mount_result.stderr}")
        distr_move_error_logger.error("Не удалось смонтировать файловую шару. Код возврата: %s. Ошибка: %s", mount_result.returncode, mount_result.stderr)
        return False
    else:
        print("Файловая шара успешно смонтирована.")
        distr_move_info_logger.info('Файловая шара успешно смонтирована.')
        return True

def unmount_share(mount_point):
    # Уберём монтирование диска
    unmount_cmd = f"umount {mount_point}"
    unmount_result = subprocess.run(unmount_cmd, shell=True, stderr=subprocess.PIPE, text=True, check=False, timeout=30)
    # Проверяем, получилось или нет
    if unmount_result.returncode != 0:
        print(f"Не удалось размонтировать файловую шару. Код возврата: {unmount_result.returncode}. Ошибка: {unmount_result.stderr}")
        distr_move_error_logger.error("Не удалось размонтировать файловую шару. Код возврата: %s. Ошибка: %s", unmount_result.returncode, unmount_result.stderr)
    else:
        print("Файловая шара успешно размонтирована.")
        distr_move_info_logger.info('Файловая шара успешно размонтирована.')

def move_distr_file(version):
    """Функция мув дистр на NextCloud"""
    # Создаем папку с названием версии на NextCloud
    create_nextcloud_folder(f"1. Актуальный релиз/Дистрибутив/{version}", NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
    # Путь к папке с дистрибутивом на файловой шаре
    distributive_folder = f"/mnt/windows_share/{version}/Release/Mainstream"
    # Ищем файл с расширением .exe в папке с дистрибутивами
    executable_file = None
    try:
        for file in os.listdir(distributive_folder):
            if file.endswith(".exe"):
                executable_file = file
                break
    except FileNotFoundError:
        print(f"Не удалось найти папку {distributive_folder}. Проверьте доступность файловой шары.")
    except OSError as error:
        print(f"Произошла ошибка при чтении папки {distributive_folder}: {error}")
    except Exception as error:
        print(f"Произошла ошибка при поиске файла дистрибутива с расширением .exe: {error}")
    if executable_file is not None:
        # Формируем пути к файлу на файловой шаре и на NextCloud
        local_file_path = os.path.join(distributive_folder, executable_file)
        remote_file_path = f"/1. Актуальный релиз/Дистрибутив/{version}/{executable_file}"
        remote_file_path = quote(remote_file_path, safe="/")  # Кодируем URL-путь
        # Загружаем файл на NextCloud
        upload_to_nextcloud(local_file_path, remote_file_path, NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)
    else:
        print("Не удалось найти файл дистрибутива с расширением .exe")

def move_distr_and_manage_share(version):
    # Монтируем шару
    if mount_share(share_path, mount_point):
        try:
            # Перемещаем дистрибутив на NextCloud
            move_distr_file(version)
        finally:
            # Размонтируем шару
            unmount_share(mount_point)
