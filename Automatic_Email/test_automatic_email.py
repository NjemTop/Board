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

def send_test_email(version):
    try:
        # Указываем путь к файлу с данными
        CONFIG_FILE = "./Main.config"
        # Открываем файл и загружаем данные
        with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as json_file:
            data_config = json.load(json_file)
            mail_settings = data_config['MAIL_SETTINGS_SUPPORT']

        # Создание письма
        msg = MIMEMultipart()
        msg['From'] = mail_settings['FROM']
        msg['To'] = 'adenalka@gmail.com'
        msg['Subject'] = 'Обновление BoardMaps {}'.format(version)

        # Загрузка и обработка HTML шаблона
        with open('HTML/index.html', 'r') as file:
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

        # Отправка письма
        with smtplib.SMTP(mail_settings['SMTP'], 587) as server:
            server.starttls()
            server.login(mail_settings['USER'], mail_settings['PASSWORD'])
            server.send_message(msg)
            print("Тестовое письмо отправлено успешно.")

    except Exception as error_message:
        print(f"Произошла ошибка при отправке тестового письма: {error_message}")


# Вызываем функцию отправки тестового письма
send_test_email(2.65)
