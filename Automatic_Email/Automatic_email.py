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
from .log_config import setup_logger, get_abs_log_path

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
        # Загрузка настроек почты
        with open('Main.config') as json_file:
            data = json.load(json_file)
            mail_settings = data['MAIL_SETTINGS']
            
        # Авторизация
        auth = ('admin', 'ekSkaaiWnK')
        response = requests.get('http://194.37.1.214:3030/api/clients_list', auth=auth)

        # Проверка статуса ответа
        if response.status_code == 200:
            clients_data = response.json()
        else:
            print(f"Сервер с данными о клиентах недоступен. Код ошибки:", response.status_code)
            bot_error_logger.error("Сервер с данными о клиентах недоступен. Код ошибки: %s", response.status_code)

        # Загрузка и обработка HTML шаблона
        with open('HTML/index.html', 'r') as file:
            html = file.read().replace('NUMBER_VERSION', str(version))

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
                
                # Подготовка письма
                msg = MIMEMultipart()
                msg['From'] = mail_settings['FROM']
                msg['To'] = ', '.join(to)
                msg['Cc'] = ', '.join(cc)
                msg['Subject'] = Header(f'Обновление BoardMaps {version}', 'utf-8')

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


                # Отправка POST-запроса
                post_data = {
                    "date": datetime.now().strftime('%Y-%m-%d'), # сегодняшняя дата
                    "release_number": version, # номер релиза
                    "client_name": client['client_name'], # имя клиента
                    "main_contact": ', '.join(to), # основной контакт
                    "copy_contact": ', '.join(cc) # копия контакта
                }
                post_response = requests.post('http://194.37.1.214:3030/api/data_release/', json=post_data, auth=auth)
                if post_response.status_code != 201:
                    print(f"Ошибка при отправке POST-запроса. Код ошибки:", post_response.status_code)
                    bot_error_logger.error("Ошибка при отправке POST-запроса. Код ошибки: %s", post_response.status_cod)
                else:
                    print(f"POST-запрос успешно отправлен и данные о рассылке сохранены в БД")

    except Exception as error_message:
        print(f"Произошла общая ошибка: {error_message}")
        bot_error_logger.error("Произошла общая ошибка: %s", error_message)

# временном запускаем функцию из файла
# send_notification(2.63)
