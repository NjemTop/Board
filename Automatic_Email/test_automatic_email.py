import requests
import json
import os
import imghdr
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from email.utils import make_msgid
# from scripts.Automatic_Email.Confluence_get_info import get_release_notes
# from scripts.Automatic_Email.Confluence_add_info import update_html_for_release

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

from bs4 import BeautifulSoup
import json

def update_html_for_release(version, release_notes):
    try:
        # Открываем HTML файл
        with open('HTML/index_2x.html', 'r', encoding='utf-8') as html_file:
            html_content = html_file.read()

        # Создаем объект BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')

        # Находим все места для вставки данных
        server_blocks = soup.find_all('h2')
        mobile_blocks = soup.find_all('h2', text='Обновление мобильного приложения')

        print("Вывод сервер блока:",server_blocks)

        # Первый блок "Обновление сервера"
        for block in server_blocks:
            if 'Обновление сервера' in block.text:
                server_block = block.find_next('tbody')
                print("Нашли сервер блока:", server_block)
                # Вставляем данные
                for note in release_notes[0]:
                    tr = soup.new_tag('tr')
                    td1 = soup.new_tag('td')
                    td1.string = '—'
                    td2 = soup.new_tag('td')
                    td2.string = note
                    tr.append(td1)
                    tr.append(td2)
                    server_block.append(tr)

        # Второй блок "Обновление мобильного приложения"
        if mobile_blocks:
            mobile_block = mobile_blocks[0].find_next('tbody')

            # Вставляем данные
            for note in release_notes[1]:
                tr = soup.new_tag('tr')
                td1 = soup.new_tag('td')
                td1.string = '—'
                td2 = soup.new_tag('td')
                td2.string = note
                tr.append(td1)
                tr.append(td2)
                mobile_block.append(tr)

        # Сохраняем обновленное содержимое в HTML файл
        with open('HTML/index.html', 'w', encoding='utf-8') as html_file:
            html_file.write(str(soup))
    except Exception as error_message:
        print(f"Произошла ошибка при обновлении HTML файла: {error_message}")


def send_test_email(version, email_send):
    try:
        # Указываем путь к файлу с данными
        CONFIG_FILE = "./Main.config"
        # Открываем файл и загружаем данные
        with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as json_file:
            data_config = json.load(json_file)
            mail_settings = data_config['MAIL_SETTINGS_SUPPORT']

        # Добавьте адрес электронной почты для скрытой копии
        bcc_email = mail_settings['FROM']

        # Создание письма
        msg = MIMEMultipart()
        msg['From'] = mail_settings['FROM']
        msg['To'] = email_send
        msg['Subject'] = 'Обновление BoardMaps {}'.format(version)

        # Добавление скрытой копии
        msg['Bcc'] = bcc_email

        # Запрос уведомления о доставке
        msg['Disposition-Notification-To'] = mail_settings['FROM']

        # Запрос уведомления о прочтении
        msg['Return-Receipt-To'] = mail_settings['FROM']
        msg['X-Confirm-Reading-To'] = mail_settings['FROM']
        msg['X-MS-Read-Receipt-To'] = mail_settings['FROM']

        # Создание Message-ID для отслеживания
        msg_id = make_msgid()
        msg['Message-ID'] = msg_id

        # Получаем информацию о релизе
        release_notes = get_release_notes(version)
        print(release_notes)

        # Загрузка и обработка HTML шаблона
        with open('HTML/index_3x.html', 'r') as file:
            html = file.read().replace('NUMBER_VERSION', str(version))
        msg.attach(MIMEText(html, 'html'))

        # Добавление изображений для CID картинок в шаблоне HTML
        images_dir = 'HTML/Images'
        for image in os.listdir(images_dir):
            image_path = os.path.join(images_dir, image)
            if os.path.isfile(image_path):
                with open(image_path, 'rb') as f:
                    img = MIMEImage(f.read(), name=os.path.basename(image))
                    img.add_header('Content-ID', '<{}>'.format(image))
                    msg.attach(img)

        # Вложение PDF файлов
        attachments_dir = 'HTML/attachment'
        if os.path.isdir(attachments_dir):
            for attachment in os.listdir(attachments_dir):
                attachment_path = os.path.join(attachments_dir, attachment)
                if os.path.isfile(attachment_path):
                    with open(attachment_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
                        msg.attach(part)

        # Вызов функции обновления HTML перед отправкой письма
        # update_html_for_release(version, release_notes)

        # Отправка письма
        with smtplib.SMTP(mail_settings['SMTP'], 587) as server:
            server.starttls()
            server.login(mail_settings['USER'], mail_settings['PASSWORD'])
            server.send_message(msg)
            print("Тестовое письмо отправлено успешно.")

        # Проверка наличия уведомлений о доставке и прочтении
        if 'Disposition-Notification-To' in msg and 'Return-Receipt-To' in msg:
            delivery_status = server.esmtp_features.get('8bitmime', False)
            read_receipt = server.esmtp_features.get('dsn', False)
            if delivery_status:
                print("Запросы уведомлений о доставке поддерживаются.")
            if read_receipt:
                print("Запросы уведомлений о прочтении поддерживаются.")

    except Exception as error_message:
        print(f"Произошла ошибка при отправке тестового письма: {error_message}")


# Вызываем функцию отправки тестового письма
# send_test_email(2.68, 'adenalka@gmail.com')
