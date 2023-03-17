import os
import subprocess
import json
from pathlib import Path
from YandexDocsMove import create_nextcloud_folder, upload_to_nextcloud

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"
# Открываем файл и загружаем данные
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    data = json.load(file)

# Получаем учётные данные из конфиг-файла
username = data["FILE_SHARE"]["USERNAME"]
password = data["FILE_SHARE"]["PASSWORD"]
domain = data["FILE_SHARE"]["DOMAIN"]

# Получаем данные для доступа к NextCloud из конфиг-файла
nextcloud_url = data["NEXT_CLOUD"]["URL"]
nextcloud_username = data["NEXT_CLOUD"]["USER"]
nextcloud_password = data["NEXT_CLOUD"]["PASSWORD"]

# Задаем параметры файловой шары
share_path = r"\\corp.boardmaps.com\data\Releases\[Server]"
mount_point = "/mnt/windows_share"

print(username)
print(password)
print(domain)
# Монтируем файловую шару
# mount_cmd = f"sudo mount -t cifs {share_path} {mount_point} -o username={username},password={password}"
mount_cmd = f"sudo mount -t cifs //corp.boardmaps.com/data/Releases /mnt/windows_share -o username={username},password={password}"
mount_result = subprocess.run(mount_cmd, shell=True, stderr=subprocess.PIPE, text=True, check=False, timeout=30)

if mount_result.returncode != 0:
    print(f"Не удалось смонтировать файловую шару. Код возврата: {mount_result.returncode}. Ошибка: {mount_result.stderr}")
else:
    print("Файловая шара успешно смонтирована.")

# Версия, которую нужно скопировать
version = "2.61"

# Создаем папку с названием версии на NextCloud
create_nextcloud_folder(f"1. Актуальный релиз/Дистрибутив/{version}", nextcloud_url, nextcloud_username, nextcloud_password)

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
    remote_file_path = f"1. Актуальный релиз/Дистрибутивы/{version}/{executable_file}"

    # Загружаем файл на NextCloud
    upload_to_nextcloud(local_file_path, remote_file_path, nextcloud_url, nextcloud_username, nextcloud_password)
else:
    print("Не удалось найти файл дистрибутива с расширением .exe")
