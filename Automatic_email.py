import json
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
import smtplib
import os

def send_notification(version):
    # Загрузка конфигураций
    with open('Main.config', 'r') as f:
        config = json.load(f)
    
    mail_settings = config['MAIL_SETTINGS']

    # Авторизация
    auth = ('admin', 'ekSkaaiWnK')
    response = requests.get('http://195.2.80.251:8137/api/clients_list', auth=auth)

    # Проверка статуса ответа
    if response.status_code == 200:
        clients_data = response.json()
        
        # Открытие и чтение шаблона HTML
        with open('HTML/index.html', 'r') as f:
            html_template = f.read()

        # Замена NUMBER_VERSION на заданную версию
        html_template = html_template.replace('NUMBER_VERSION', str(version))

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
                msg = MIMEMultipart('related')
                msg['Subject'] = Header('Notification', 'utf-8')
                msg['From'] = mail_settings['FROM']
                msg['To'] = ', '.join(to)
                msg['Cc'] = ', '.join(cc)

                # Добавление HTML
                msg.attach(MIMEText(html_template, 'html'))

                # Добавление изображений
                for image_file in ["bm_logo.png", "done.png", "download.png", "gear.png", "mail_alert.png", "mail.png"]:
                    with open(f'HTML/Images/{image_file}', 'rb') as f:
                        msg_image = MIMEImage(f.read())
                        msg_image.add_header('Content-ID', f'<{image_file}>')
                        msg.attach(msg_image)

                # Отправка письма
                with smtplib.SMTP(mail_settings['SMTP'], 587) as server:
                    server.starttls()
                    server.login(mail_settings['USER'], mail_settings['PASSWORD'])
                    server.send_message(msg)
                    print(f"Mail has been sent to {', '.join(to)} with CC to {', '.join(cc)}")

send_notification(2.63)
