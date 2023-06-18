import requests

def transfer_data(old_endpoint, new_endpoint, auth):
    response = requests.get(old_endpoint, auth=auth)

    if response.status_code == 200:
        clients_data = response.json()

        for client_data in clients_data:
            # Удаление поля id из основного объекта клиента
            if "id" in client_data:
                del client_data["id"]

            # Удаление полей id из всех подобъектов клиента
            for subfield in client_data:
                if type(client_data[subfield]) is list:  # Проверка, является ли поле списком объектов
                    for item in client_data[subfield]:
                        if "id" in item:
                            del item["id"]
                        
            post_response = requests.post(new_endpoint, json=client_data, auth=auth)
            
            if post_response.status_code != 201:
                print(f"Ошибка трансфера клиента {client_data.get('client_name')}. Ошибка: {post_response.text}")
            else:
                print(f"Миграция клиента {client_data.get('client_name')} успешно завершена.")

    else:
        print(f"Ошибка получения данных с сервера. Ошибка: {response.text}")


old_endpoint = "http://195.2.80.251:8137/api/clients/"
new_endpoint = "http://10.6.75.81:8137/api/add_client"

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"
# Открываем файл и загружаем данные
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    data = json.load(file)

# Получаем учётные данные из конфиг-файла
CREG_USERNAME = data["CREG"]["USERNAME"]
CREG_PASSWORD = data["CREG"]["PASSWORD"]

auth = (CREG_USERNAME, CREG_PASSWORD)

transfer_data(old_endpoint, new_endpoint, auth)
