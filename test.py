import requests
import json

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"
# Открываем файл и загружаем данные
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    data = json.load(file)

# Получаем учётные данные из конфиг-файла
CREG_USERNAME = data["CREG"]["USERNAME"]
CREG_PASSWORD = data["CREG"]["PASSWORD"]

# Параметры авторизации
source_auth = (CREG_USERNAME, CREG_PASSWORD)
target_auth = (CREG_USERNAME, CREG_PASSWORD)

# URL-адреса
source_url = 'http://195.2.80.251:8137/api/data_release/2.65/version_info'
target_url = 'http://10.6.75.81:8137/api/data_release/'

# Получение данных с исходного сервера
response = requests.get(source_url, auth=source_auth)

# Проверка статуса ответа
if response.status_code == 200:
    source_data = response.json()
else:
    print(f"Не удалось получить данные с исходного сервера. Код ошибки: {response.status_code}")
    exit(1)

# Преобразование данных в требуемый формат и отправка на целевой сервер
for item in source_data:
    transformed_item = {
        'date': '2023-07-18',  # Замена даты
        'release_number': 2.65,
        'client_name': item['client_name'],
        'main_contact': item['main_contact'],
        'copy_contact': item['copy_contact']
    }

    # Отправка каждого объекта данных на целевой сервер по отдельности
    response = requests.post(target_url, json=transformed_item, auth=target_auth)

    # Проверка статуса ответа
    if response.status_code == 200 or response.status_code == 201:
        print(f"Данные по клиенту {item['client_name']} успешно отправлены на целевой сервер.")
    else:
        print(f"Не удалось отправить данные по клиенту {item['client_name']} на целевой сервер. Код ошибки: {response.text}")
