from atlassian import Confluence
from bs4 import BeautifulSoup
import json

def get_release_notes(version):
    # Указываем путь к файлу с данными
    CONFIG_FILE = "Main.config"
    # Открываем файл и загружаем данные
    with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
        data = json.load(file)

    # Получаем учётные данные из конфиг-файла для доступа к Confluence
    USERNAME = data["FILE_SHARE"]["USERNAME"]
    PASSWORD = data["FILE_SHARE"]["PASSWORD"]

    # Адрес Confluence
    url = 'https://confluence.boardmaps.ru'

    try:
        # Создаем объект Confluence
        confluence = Confluence(
            url=url,
            username=USERNAME,
            password=PASSWORD)
    except Exception as error_message:
        print(f"Не удалось создать объект Confluence: {str(error_message)}")
        return

    # Указываем название страниц, к которым будем переходить
    server_title = f"BM {version}"
    ipad_title = f"BM iOS/iPadOS {version}"

    try:
        # Переходим на страницу релиза и вытягиваем всю информацию со страниц
        server_page_content = confluence.get_page_by_title(title=server_title, space="development", expand='body.view')
        ipad_page_content = confluence.get_page_by_title(title=ipad_title, space="development", expand='body.view')
    except Exception as error_message:
        print(f"Не удалось получить страницы: {str(error_message)}")
        return

    if server_page_content is None:
        print(f"Статья для сервера '{server_title}' не найдена")
        return

    if ipad_page_content is None:
        print(f"Статья для iPad '{ipad_title}' не найдена")
        return

    def extract_list(page_content):
        # Создаем объект BeautifulSoup из HTML тела страницы
        soup = BeautifulSoup(page_content['body']['view']['value'], 'html.parser')

        # Находим заголовок "Текст для оповещения о новой версии"
        header = soup.find('h1', text='Текст для оповещения о новой версии')

        # Находим ближайший список <ol> или <ul> после заголовка
        list = header.find_next_sibling(['ol', 'ul'])

        # Если список найден
        if list is not None:
            # Итерируемся по каждому пункту списка и печатаем его
            return [item.text.strip() for item in list.find_all('li')]
        else:
            return ["Не найден список после заголовка."]

    return extract_list(server_page_content), extract_list(ipad_page_content)

# server_notes, ipad_notes = get_release_notes("2.68")
# print("Server Release Notes:")
# for note in server_notes:
#     print(note)
# print("\niPad Release Notes:")
# for note in ipad_notes:
#     print(note)
