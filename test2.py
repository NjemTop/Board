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
                print(f"Failed to transfer client {client_data.get('client_name')}. Error: {post_response.text}")
            else:
                print(f"Successfully migrated client {client_data.get('client_name')}.")

    else:
        print(f"Failed to get data from old server. Error: {response.text}")


old_endpoint = "http://195.2.80.251:8137/api/clients/"
new_endpoint = "http://10.6.75.81:8137/api/add_client"
auth = ('admin', 'ekSkaaiWnK')

transfer_data(old_endpoint, new_endpoint, auth)
