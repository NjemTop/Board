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
from scripts.Automatic_Email.Confluence_get_info import get_release_notes


# Указываем настройки логов для нашего файла с классами
bot_error_logger = setup_logger('TeleBot', get_abs_log_path('bot-errors.log'), logging.ERROR)
bot_info_logger = setup_logger('TeleBot', get_abs_log_path('bot-info.log'), logging.INFO)


def format_updates_to_html(updates):
    html_updates = ''
    for update in updates:
        html_updates += f'<tr><td style="padding-right: 8px; vertical-align: top;">—</td><td>{update}</td></tr>'
    return html_updates


def send_notification(version, email_send, mobile_version=None):
    """
    Функция по отправке рассылки клиентам.
    Информация берётся из сервиса Creg, в котором есть перечень клиентов,
    кому отправлять рассылку. Перебираються клиенты и перебираются контакты,
    находится "Основной" и "Копия" кому отправляется письмо с рассылкой.
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

        # Определение шаблона и URL сервиса Creg на основе версии
        version_prefix = version.split('.')[0]
        if version_prefix == '2':
            template_file = 'HTML/index_2x.html'
            creg_url = 'https://creg.boardmaps.ru/api/version2_clients'
        elif version_prefix == '3':
            template_file = 'HTML/index_3x.html'
            creg_url = 'https://creg.boardmaps.ru/api/version3_clients'
            # Проверяем есть ли заполненный аргумент для мобильной версии
            if mobile_version is None:
                # Если не заполнен, тогда указываем как у сервера (для 2.х версий)
                mobile_version = version
        else:
            bot_error_logger.error("Шаблон для версии: %s не найден", version)
            raise

        # Получаем информацию о релизе
        server_updates, ipad_updates = get_release_notes(version, mobile_version)

        # Форматирование обновлений в HTML
        server_updates_html = format_updates_to_html(server_updates)
        ipad_updates_html = format_updates_to_html(ipad_updates)

        # Загрузка и обработка HTML шаблона
        with open(template_file, 'r') as file:
            html = file.read()
            html = html.replace('NUMBER_VERSION', str(version))
            html = html.replace('<!--SERVER_UPDATES-->', server_updates_html)
            html = html.replace('<!--IPAD_UPDATES-->', ipad_updates_html)
            
        # Авторизация в систему крег
        auth = (CREG_USERNAME, CREG_PASSWORD)
        # Получаем данные для определения информации кому отправлять рассылку
        response = requests.get(creg_url, auth=auth)

        # Проверка статуса ответа
        if response.status_code == 200:
            clients_data = response.json()
        else:
            bot_error_logger.error("Сервер с данными о клиентах недоступен. Код ошибки: %s", response.status_code)

        # Перебор клиентов
        for client in clients_data:
            try:
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
                        bot_info_logger.info("Нет контактов для клиента %s. Пропускаем.", {client['client_name']})
                        continue

                    # Подготовка письма
                    msg = MIMEMultipart()
                    msg['From'] = mail_settings['FROM']
                    msg['To'] = ', '.join(to)
                    msg['Cc'] = ', '.join(cc)
                    msg['Subject'] = Header(f'Обновление BoardMaps {version}', 'utf-8')
                    # Добавьте адрес электронной почты для скрытой копии
                    msg['Bcc'] = mail_settings['FROM']

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
                        bot_error_logger.error("Файлы в папке «вложения» не найдены.")
                        break

                    # Отправка письма
                    with smtplib.SMTP(mail_settings['SMTP'], 587) as server:
                        server.starttls()
                        server.login(mail_settings['USER'], mail_settings['PASSWORD'])
                        server.send_message(msg)
                        bot_info_logger.info("Почта была отправлена ​​на %s с копией на %s", {', '.join(to)}, {', '.join(cc)})

                    # Отправка POST-запроса
                    post_data = {
                        "date": datetime.now().strftime('%Y-%m-%d'), # сегодняшняя дата
                        "release_number": version, # номер релиза
                        "client_name": client['client_name'], # имя клиента
                        "main_contact": ', '.join(to), # основной контакт
                        "copy_contact": ', '.join(cc) # копия контакта
                    }
                    post_response = requests.post('https://creg.boardmaps.ru/api/data_release/', json=post_data, auth=auth)
                    if post_response.status_code != 201:
                        bot_error_logger.error("Ошибка при отправке POST-запроса. Сообщение об ошибке: %s", post_response.text)
                    else:
                        bot_info_logger.info("POST-запрос успешно отправлен и данные о рассылке сохранены в БД")

                    time.sleep(180) # Задержка в 3 минуты после каждого отправленного письма
            except Exception as error_message:
                bot_error_logger.error("Ошибка при обработке клиента %s: %s", client['client_name'], error_message)
                # Пропуск текущего клиента и переход к следующему
                continue

    except Exception as error_message:
        bot_error_logger.error("Произошла общая ошибка: %s", error_message)
