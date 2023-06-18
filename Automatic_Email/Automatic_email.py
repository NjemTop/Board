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
import logging
from logger.log_config import setup_logger, get_abs_log_path
import time

# Указываем настройки логов для нашего файла с классами
bot_error_logger = setup_logger('TeleBot', get_abs_log_path('bot-errors.log'), logging.ERROR)
bot_info_logger = setup_logger('TeleBot', get_abs_log_path('bot-info.log'), logging.INFO)

def send_notification(version):
    """
    Функция по отправке рассылки клиентам.
    Информация берёться из сервиса Краг, в котором есть перечень клиентов,
    кому отправлять рассылку. Перебираються клиенты и перебираются контакты,
    находиться "Основной" и "Копия" кому отправляется письмо с рассылкой.
    На себя принимает параметр version, который подставляеться в HTML шаблон,
    вместо аргумента "NUMBER_VERSION".
    """
    try:
        # Указываем путь к файлу с данными
        CONFIG_FILE = "./Main.config"
        # Открываем файл и загружаем данные
        with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as json_file:
            data_config = json.load(json_file)
            mail_settings = data_config['MAIL_SETTINGS_SUPPORT']
            CREG_USERNAME = data_config['CREG']['USERNAME']
            CREG_PASSWORD = data_config['CREG']['PASSWORD']
            
        # Авторизация в систему крег
        auth = (CREG_USERNAME, CREG_PASSWORD)
        # Получаем данные для определения информации кому отправлять рассылку
        response = requests.get('http://195.2.80.251:8137/api/clients_list', auth=auth)

        # Проверка статуса ответа
        if response.status_code == 200:
            clients_data = response.json()
        else:
            print(f"Сервер с данными о клиентах недоступен. Код ошибки:", response.status_code)
            bot_error_logger.error("Сервер с данными о клиентах недоступен. Код ошибки: %s", response.status_code)

        # Перебор клиентов
        for client in clients_data:
            if client['contact_status']:
                to = []
                cc = []

                # Перебор контактов
                for contact in client['contacts_card']:
                    if contact['notification_update'] == "Основной":
                        to.append(contact['contact_email'])
                    elif contact['notification_update'] == "Копия":
                        cc.append(contact['contact_email'])

                # Если список "to" и "cc" пустые, пропускаем эту итерацию цикла
                if not to and not cc:
                    print(f"Нет контактов для клиента {client['client_name']}. Пропускаем.")
                    bot_info_logger.info("Нет контактов для клиента %s. Пропускаем.", {client['client_name']})
                    continue

                # Подготовка письма
                msg = MIMEMultipart()
                msg['From'] = mail_settings['FROM']
                msg['To'] = ', '.join(to)
                msg['Cc'] = ', '.join(cc)
                msg['Subject'] = Header(f'Обновление BoardMaps {version}', 'utf-8')

                # Загрузка и обработка HTML шаблона
                with open('HTML/index.html', 'r') as file:
                    html = file.read().replace('NUMBER_VERSION', str(version))
                    html = html.replace('COPY_EMAIL', ', '.join(cc))

                # Добавление HTML шаблона
                msg.attach(MIMEText(html, 'html'))

                # Добавление изображений для CID картинок в шаблоне HTML
                images_dir = 'HTML/Images'
                for image in os.listdir(images_dir):
                    image_path = os.path.join(images_dir, image)
                    if imghdr.what(image_path):
                        with open(image_path, 'rb') as f:
                            img = MIMEImage(f.read(), name=os.path.basename(image))
                            img.add_header('Content-ID', '<{}>'.format(image))
                            msg.attach(img)
                    else:
                        print(f"Файл '{image}' в каталоге «Изображения» не является файлом изображения.")
                        bot_error_logger.error("Файл %s в каталоге «Изображения» не является файлом изображения.", response.status_code)
                        break

                # Вложение PDF файлов
                attachments_dir = 'HTML/attachment'
                if os.listdir(attachments_dir): # Проверка на наличие файлов в папке
                    for attachment in os.listdir(attachments_dir):
                        with open(os.path.join(attachments_dir, attachment), 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment))
                            msg.attach(part)
                else:
                    print("Файлы в папке «вложения» не найдены.")
                    bot_error_logger.error("Файлы в папке «вложения» не найдены.")
                    break

                # Отправка письма
                with smtplib.SMTP(mail_settings['SMTP'], 587) as server:
                    server.starttls()
                    server.login(mail_settings['USER'], mail_settings['PASSWORD'])
                    server.send_message(msg)
                    print(f"Почта была отправлена ​​на {', '.join(to)} с копией на {', '.join(cc)}")
                    bot_info_logger.info("Почта была отправлена ​​на %s с копией на %s", {', '.join(to)}, {', '.join(cc)})
                    time.sleep(30) # Задержка в 30 секунду после каждого отправленного письма

                # Отправка POST-запроса
                post_data = {
                    "date": datetime.now().strftime('%Y-%m-%d'), # сегодняшняя дата
                    "release_number": version, # номер релиза
                    "client_name": client['client_name'], # имя клиента
                    "main_contact": ', '.join(to), # основной контакт
                    "copy_contact": ', '.join(cc) # копия контакта
                }
                post_response = requests.post('http://195.2.80.251:8137/api/data_release/', json=post_data, auth=auth)
                if post_response.status_code != 201:
                    print(f"Ошибка при отправке POST-запроса. Сообщение об ошибке:", post_response.text)
                    bot_error_logger.error("Ошибка при отправке POST-запроса. Сообщение об ошибке: %s", post_response.text)
                else:
                    print(f"POST-запрос успешно отправлен и данные о рассылке сохранены в БД")
                    bot_info_logger.info("POST-запрос успешно отправлен и данные о рассылке сохранены в БД")

    except Exception as error_message:
        print(f"Произошла общая ошибка: {error_message}")
        bot_error_logger.error("Произошла общая ошибка: %s", error_message)
