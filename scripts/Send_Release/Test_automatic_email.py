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
from scripts.Automatic_Email.Confluence_get_info import get_release_notes


def format_updates_to_html(updates):
    html_updates = ''
    for update in updates:
        html_updates += f'<tr><td style="padding-right: 8px; vertical-align: top;">—</td><td>{update}</td></tr>'
    return html_updates

def send_test_email(version, email_send, mobile_version=None):
    try:
        # Проверяем есть ли заполненный аргумент для мобильной версии
        if mobile_version is None:
            # Если не заполнен, тогда указываем как у сервера (для 2.х версий)
            mobile_version = version

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
        server_updates, ipad_updates = get_release_notes(version, mobile_version)

        # Форматирование обновлений в HTML
        server_updates_html = format_updates_to_html(server_updates)
        ipad_updates_html = format_updates_to_html(ipad_updates)

        # Определение шаблона на основе версии
        version_prefix = version.split('.')[0]  # Получаем первую цифру версии
        if version_prefix == '2':
            template_file = 'HTML/index_2x.html'
        elif version_prefix == '3':
            template_file = 'HTML/index_3x.html'
        else:
            print(f"Шаблон для версии {version} не найден")
            raise

        # Загрузка и обработка HTML шаблона
        with open(template_file, 'r') as file:
            html = file.read()
            html = html.replace('NUMBER_VERSION', str(version))
            html = html.replace('<!--SERVER_UPDATES-->', server_updates_html)
            html = html.replace('<!--IPAD_UPDATES-->', ipad_updates_html)
        
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


if __name__ == "__main__":
    # Вызываем функцию отправки тестового письма
    send_test_email("3.6", 'oleg.eliseev@boardmaps.ru', "2.68")
