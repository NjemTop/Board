import encodings
import telebot
from telebot import types
import requests
import pandas as pd
import json
from bs4 import BeautifulSoup
import subprocess, sys
import pathlib
from pathlib import Path
import random
import smtplib
import multiprocessing
import xml.etree.ElementTree as ET
import logging
import os
import platform
import configparser
from writexml import create_xml

# создаем логгер
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# создаем обработчик, который будет записывать ошибки в файл bot-error.log
handler = logging.FileHandler('bot-error.log')
handler.setLevel(logging.ERROR)

# создаем форматирование
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')
handler.setFormatter(formatter)

# добавляем обработчик в логгер
logger.addHandler(handler)

# Проверяем систему, где запускается скрипт
if platform.system() == 'Windows':
    # получаем путь к директории AppData\Local для текущего пользователя
    local_appdata_path = os.environ['LOCALAPPDATA']
else:
    local_appdata_path = os.environ['HOME']


# Создаем объект configparser
config = configparser.ConfigParser()
# Читаем данные из файла
config.read('system_info.config')
# Получаем значение ключа BOT_TOKEN из секции BOT
BOT_TOKEN = config.get('BOT', 'BOT_TOKEN')
# Сохраняем значение в переменную TOKEN
TOKEN = BOT_TOKEN

## Авторизация в HappyFox
# Получаем значение ключа API и API_KEY из секции API
API_KEY = config.get('API', 'API_KEY')
API_SECRET = config.get('API', 'API_SECRET')
# Сохраняем значение в переменную auth
auth = (API_KEY, API_SECRET)
headers = {'Content-Type': 'application/json'}

# Создаем бота
bot=telebot.TeleBot(TOKEN)

#alert_chat_id = 320851571

# ФУНКЦИЯ ОТПРАВКИ АЛЕРТА В ЧАТ
def send_telegram_message(alert_chat_id, alert_text):
    """Отправляет сообщение в телеграм-бот"""
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    headers_server = {'Content-type': 'application/json'}
    data = {'chat_id': alert_chat_id, 'text': f'{alert_text}'}
    response = requests.post(url, headers=headers_server, data=json.dumps(data))
    print(response)
    print('*--*--*'*60)

    
# УРОВЕНЬ 1 проверка вызова "старт" и доступа к боту
def check_user_in_file(chat_id):
    """Функция для проверки наличия данных в файле data.xml"""
    try:
        # Открываем файл и ищем chat_id
        with open(Path('data.xml')) as user_access:
            root = ET.parse(user_access).getroot()
            for user in root.findall('user'):
                header_footer = user.find('header_footer')
                chat_id_elem = header_footer.find('chat_id')
                if chat_id_elem is not None and chat_id_elem.text == str(chat_id):
                    return True
    except FileNotFoundError as e:
        logger.error("Файл data.xml не найден: %s", e)
        print("Файл data.xml не найден")
    except Exception as e:
        logger.error("Произошла ошибка при чтении файла data.xml: %s", e)
        print("Ошибка чтения файла data.xml")
    return False

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message_start):
    """Функция запуска бота кнопкой /start, а также проверка есть ли уже УЗ"""
    if check_user_in_file(message_start.chat.id):
        # Главное меню
        main_menu = types.InlineKeyboardMarkup()
        button_clients = types.InlineKeyboardButton(text='Клиенты', callback_data='button_clients')
        button_SD_Gold_Platinum = types.InlineKeyboardButton('ServiceDes (Gold & Platinum)', callback_data='button_SD_Gold_Platinum')
        button_SD_Silver_Bronze = types.InlineKeyboardButton('ServiceDesk (Silver & Bronze)', callback_data='button_SD_Silver_Bronze')
        main_menu.add(button_clients, button_SD_Gold_Platinum, button_SD_Silver_Bronze, row_width=1)
        bot.send_message(message_start.chat.id, 'Приветствую! Выберите нужное действие', reply_markup=main_menu)
    else:
        question_email = bot.send_message(message_start.chat.id,"Привет! Пожалуйста, введите адрес рабочей почты.")
        bot.register_next_step_handler(question_email, check_email)
        
## Если пользователя нет в списке, просим его указать почту, куда будет выслан сгенерированный пароль
def check_email(email_access):
        """Функция отправки кода проверки на почту"""
        ## Если почтовый адрес содержит "@boardmaps.ru"
        if '@boardmaps.ru' in email_access.text:
            ## Отправляем сообщение
            ## Логин и пароль от почты, которой отправляется письмо
            email = 'sup-smtp@boardmaps.ru'
            password_0 = 'rcjtcxvjzfsjglko'
            ## Настройки SMTP сервера
            server = smtplib.SMTP('smtp.yandex.ru', 587)
            server.ehlo()
            server.starttls()
            server.login(email, password_0)
            ## Генерируем рандомный пароль для доступа к боту
            global password
            password = ''
            for _ in range(12):
                password = password + random.choice(list('1234567890abcdefghigklmnopqrstuvyxwzABCDEFGHIGKLMNOPQRSTUVYXWZ!@#$%^&*()_+'))
            ## Данные (кому отправлять, какая тема и письмо)
            dest_email = email_access.text
            subject = 'Message from chatbot'
            email_text = password
            message = 'From: %s\nTo: %s\nSubject: %s\n\n%s' % (email, dest_email, subject, email_text)
            ## Сама отправка письма используя ранее разначенные аргументы
            server.sendmail(email, dest_email, message)
            server.quit()
            ## Бот выдает сообщение с просьбой ввести пароль + вносим почту пользователя в БД
            password_message = bot.send_message(email_access.chat.id,"Пожалуйста, введите пароль, отправленный на указанную почту.")
            bot.register_next_step_handler(password_message, check_pass_answer)
            url = ('https://boardmaps.happyfox.com/api/1.1/json/staff/')
            res = requests.get(url, auth=auth, headers=headers).json()
            for i in range(len(res)):
                res_i = res[i]
                find_email = res_i.get('email')
                if find_email == email_access.text:
                    global find_id_HF
                    find_id_HF = res_i.get('id')
                    global email_access_id
                    email_access_id = find_email
                    global find_name
                    find_name = res_i.get('name')
                    global find_role_id
                    find_role = res_i.get('role') 
                    find_role_id = find_role.get('id')
                else:
                    continue     
        else:
            bot.send_message(email_access.chat.id, 'К сожалению, не могу предоставить доступ.')
## Проверяем введенный пользователем пароль
def check_pass_answer(password_message):
    """Функция проверки пароля и записи УЗ в data.xml"""
    ## Если пароль подходит
    if password_message.text == password:
        ## ВРЕМЕННЫЙ АРГУМЕНТ роли
        find_role = 'Admin'
        ## Создаем XML файл и записываем данные
        create_xml(email_access_id, find_id_HF, find_name, find_role, find_role_id, password_message.chat.id)
        
        ## Показываем пользователю главное меню
        main_menu = types.InlineKeyboardMarkup()
        button_clients = types.InlineKeyboardButton(text= 'Клиенты', callback_data='button_clients')
        button_SD_Gold_Platinum = types.InlineKeyboardButton('ServiceDes (Gold & Platinum)', callback_data='button_SD_Gold_Platinum')
        button_SD_Silver_Bronze = types.InlineKeyboardButton('ServiceDesk (Silver & Bronze)', callback_data='button_SD_Silver_Bronze')
        main_menu.add(button_clients, button_SD_Gold_Platinum, button_SD_Silver_Bronze, row_width=1)
        bot.send_message(password_message.chat.id, 'Приветствую! Выберите нужное действие', reply_markup=main_menu)
    else:
        bot.send_message(password_message.chat.id, 'Неправильный пароль.')

#уведомления о новых тикетах
@bot.message_handler(commands=['alert'])
def alert_message(message_alert):
    if message_alert.chat.id not in users:
        bot.send_message(message_alert.chat.id,"К сожалению, у Вас отсутствует доступ.")
    else:
######## АЛЕРТЫ ПО НОВЫМ ТИКЕТАМ БЕЗ ОТВЕТА
### ЗАДАЁМ ПАРАМЕТРЫ ЗАПРОСА, ЧТОБЫ СРАЗУ ВЫДАТЬ ИНФУ О НОВОМ СОЗДАННОМ ТИКЕТЕ СО СТАТУСОМ NEW В КАТЕГОРИИ СТАНДАРТНОЙ И БЕЗ НАЗНАЧЕННОГО НА ДАННЫЙ ТИКЕТ
        query_params = { "status": '1', "category": '1', "unresponded": 'true', "q": 'assignee:"none"'}
        ### ЗАДАЁМ ENDPOINTS, ПАРОЛИ И ВЫТЯГИВАЕМ ВСЮ ИНФУ ИЗ ЗАПРОСА
        url_0 = ('https://boardmaps.happyfox.com/api/1.1/json/tickets/?size=50&page=1')
        res_0 = requests.get(url_0,auth=auth, headers=headers, params=query_params).json()
        ### ВЫТАСКИВАЕМ ИНФУ о количестве отфильтрованных тикетов ИЗ МАССИВА page_info
        page_info = res_0.get('page_info')
        last_index = page_info.get('last_index')
        # делаем проверку по количеству найденных тикетов
        if last_index == 0:
            print('No tickets')
            # если тикеты есть. если 1, то проверяем один. Если больше, то запускается цикл перебора тикетов с выводом инфы для каждого тикета построчно
        elif last_index >= 1:
            for page in range(len(str(last_index))):
                if page == 0:
                    url = url_0
                    res = res_0
                # каждый тикет будет на отдельной странице, т.е. № тикета = номеру страницы. перебираем стр по тикетам
                else:
                    url = ('https://boardmaps.happyfox.com/api/1.1/json/tickets/?size=50&page=' + (page + 1))
                    res = requests.get(url,auth=auth, headers=headers, params=query_params).json()
            ### ВЫТАСКИВАЕМ всю ИНФУ по тикету ИЗ МАССИВА DATA и из вложенного в него списка
            data = res.get('data')
            for i in range (len(data)):
                ticket_data = data[i]
                # находим тему
                ticket_subject = ticket_data.get('subject')
                # находим тикет айди
                ticket_id=ticket_data.get('id')
                ticket_url = str('https://boardmaps.happyfox.com/staff/ticket/' + str(ticket_id))
                ticket_link = '[' + str(ticket_id) + '](' + ticket_url + ')'
                # находим приоритет из дата - приорити инфо - приорити нейм
                priority_info = ticket_data.get('priority')
                priority_name = priority_info.get('name')
                # ищем название клиента внутри юзер инфо - контакт инфо - нейм
                user_info = ticket_data.get('user')
                contact_info = user_info.get('contact_groups')
                ## ищем имя внутри списка контакт инфо []
                for k in range(len(contact_info)):
                    name_info = contact_info[k].get('name')
                # выводим на печать искомые данные
                bot.send_message(message_alert.chat.id, 'Новый тикет: ' + ticket_link + '\nКлиент: ' + str(name_info) + '\nПриоритет: ' + str(priority_name) + '\nТема: ' + str(ticket_subject), parse_mode='Markdown')

@bot.message_handler(commands=['clients'])
def clients_message(message_clients):
    if message_clients.chat.id not in users:
        bot.send_message(message_clients.chat.id,"К сожалению, у Вас отсутствует доступ.")
    else:
        button_clients = types.InlineKeyboardMarkup()
        button_list_of_clients = types.InlineKeyboardButton(text='Список клиентов', callback_data='button_list_of_clients')
        button_clients_version = types.InlineKeyboardButton(text='Версии клиентов', callback_data='button_clients_version')
        button_templates = types.InlineKeyboardButton(text='Статистика по тикетам за период (шаблоны)', callback_data='button_templates')
        button_clients.add(button_list_of_clients, button_clients_version, button_templates, row_width=2)
        bot.send_message(message_clients.chat.id, 'Какую информацию хотите получить?', reply_markup=button_clients)
@bot.message_handler(commands=['sd_sb'])
def sd_sb_message(message_sd_sb):
    if message_sd_sb.chat.id not in users:
        bot.send_message(message_sd_sb.chat.id,"К сожалению, у Вас отсутствует доступ.")
    else:
        button_SD_Silver_Bronze = types.InlineKeyboardMarkup()
        button_update_tickets_SB = types.InlineKeyboardButton(text='Обновление версии приложения (S&B)', callback_data='button_update_tickets_SB')
        button_else_SB = types.InlineKeyboardButton(text= 'Остальные тикеты (S&B)', callback_data='button_else_SB')
        button_SD_Silver_Bronze.add(button_update_tickets_SB, button_else_SB, row_width=1)
        bot.send_message(message_sd_sb.chat.id, 'Выберите раздел:', reply_markup=button_SD_Silver_Bronze)
@bot.message_handler(commands=['sd_gp'])
def sd_gp_message(message_sd_gp):
    if message_sd_gp.chat.id not in users:
        bot.send_message(message_sd_gp.chat.id,"К сожалению, у Вас отсутствует доступ.")
    else:
        button_SD_Gold_Platinum = types.InlineKeyboardMarkup()
        button_update_tickets_GP = types.InlineKeyboardButton(text='Обновление версии приложения (G&P)', callback_data='button_update_tickets_GP')
        button_else_GP = types.InlineKeyboardButton(text= 'Остальные тикеты (G&P)', callback_data='button_else_GP')
        button_SD_Gold_Platinum.add(button_update_tickets_GP, button_else_GP, row_width=1)
        bot.send_message(message_sd_gp.chat.id,"Выберите раздел:", reply_markup=button_SD_Gold_Platinum)

# Добавляем подуровни к кнопкам выше
@bot.callback_query_handler(func=lambda call: True)
def inline_button(call):
# Возврат в главное меню. Кнопки [Клиенты] / [ServiceDesk (Gold & Platinum)] / [ServiceDesk (Silver & Bronze)]
    if call.data == "mainmenu":
        main_menu = types.InlineKeyboardMarkup()
        button_clients = types.InlineKeyboardButton(text= 'Клиенты', callback_data='button_clients')
        button_SD_Gold_Platinum = types.InlineKeyboardButton('ServiceDesk (Gold & Platinum)', callback_data='button_SD_Gold_Platinum')
        button_SD_Silver_Bronze = types.InlineKeyboardButton('ServiceDesk (Silver & Bronze)', callback_data='button_SD_Silver_Bronze')
        main_menu.add(button_clients, button_SD_Gold_Platinum, button_SD_Silver_Bronze, row_width=1)
        bot.edit_message_text('Главное меню:', call.message.chat.id, call.message.message_id, reply_markup=main_menu)
    
# УРОВЕНЬ 2 "КЛИЕНТЫ". Добавляем кнопки [Список клиентов] / [Версии клиентов] / [Шаблоны]
    elif call.data == "button_clients":
        button_clients = types.InlineKeyboardMarkup()
        button_list_of_clients = types.InlineKeyboardButton(text='Список клиентов', callback_data='button_list_of_clients')
        button_clients_version = types.InlineKeyboardButton(text='Версии клиентов', callback_data='button_clients_version')
        button_templates = types.InlineKeyboardButton(text='Статистика по тикетам за период (шаблоны)', callback_data='button_templates')
        button_clients.add(button_list_of_clients, button_clients_version, button_templates, row_width=2)
        back_from_button_clients = types.InlineKeyboardButton(text='Назад', callback_data='mainmenu')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_clients.add(back_from_button_clients, main_menu, row_width=2)
        bot.edit_message_text('Какую информацию хотите получить?', call.message.chat.id, call.message.message_id,reply_markup=button_clients)
    # УРОВЕНЬ 3. Вызов кнопки "СПИСОК КЛИЕНТОВ"
    elif call.data == 'button_list_of_clients':
        button_list_of_clients = types.InlineKeyboardMarkup()
        back_from_button_list_of_clients = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_list_of_clients.add(back_from_button_list_of_clients, main_menu, row_width=2)
        bot.edit_message_text('Для просмотра списка клиентов, пожалуйста, перейдите по ссылке:\nhttps://apps.boardmaps.ru/app/creg/page1-63bd167887eafa565f728b82.', call.message.chat.id, call.message.message_id,reply_markup=button_list_of_clients)
    # УРОВЕНЬ 3 "ВЕРСИИ КЛИЕНТОВ". Добавляем кнопки [Общий список версий] / [Узнать версию клиента]
    elif call.data == "button_clients_version":
        button_clients_version = types.InlineKeyboardMarkup()
        button_version_main_list = types.InlineKeyboardButton(text='Общий список версий', callback_data='button_version_main_list')
        button_version = types.InlineKeyboardButton(text= 'Узнать версию клиента', callback_data='button_version')
        button_clients_version.add(button_version_main_list, button_version, row_width=2)
        back_from_button_clients_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_clients_version.add(back_from_button_clients_version, main_menu, row_width=2)
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_clients_version)
    ### УРОВЕНЬ 4 "ОБЩИЙ СПИСОК ВЕРСИЙ". Добавляем ссылку на список
    elif call.data == "button_version_main_list":
        button_version_main_list = types.InlineKeyboardMarkup()
        back_from_button_version_main_list = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients_version')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_version_main_list.add(back_from_button_version_main_list, main_menu, row_width=2)
        bot.edit_message_text('Для просмотра списка версий клиентов, пожалуйста, перейдите по ссылке:\nhttps://apps.boardmaps.ru/app/creg/page1-63bd167887eafa565f728b82.', call.message.chat.id, call.message.message_id,reply_markup=button_version_main_list)
    ### УРОВЕНЬ 4 "УЗНАТЬ ВЕРСИЮ КЛИЕНТА"
    elif call.data == "button_version":  
        button_version = types.InlineKeyboardMarkup()
        back_from_button_version = types.InlineKeyboardButton(text='Отмена', callback_data='button_clients_version') 
        main_menu = types.InlineKeyboardButton(text='Главное меню', callback_data='mainmenu')
        button_version.add(back_from_button_version, main_menu, row_width=2)
        test=bot.edit_message_text('Просьба отправить в чат сообщение с наименованием клиента, версию которого Вы хотите узнать.', call.message.chat.id, call.message.message_id,reply_markup=button_version)
        bot.register_next_step_handler(test,send_text_version)

    # УРОВЕНЬ 3 "ШАБЛОНЫ". Добавляем кнопки [Теле2] / [ПСБ] / [РЭЦ] / [Почта России]
    elif call.data == "button_templates": 
        button_templates = types.InlineKeyboardMarkup()
        button_tele2 = types.InlineKeyboardButton(text='Теле2', callback_data='button_tele2')
        button_psb = types.InlineKeyboardButton(text='ПСБ', callback_data='button_psb')
        button_rez = types.InlineKeyboardButton(text='РЭЦ', callback_data='button_rez')
        button_pochtaR = types.InlineKeyboardButton(text='Почта России', callback_data='button_pochtaR')
        button_templates.add(button_tele2, button_psb, button_rez, button_pochtaR, row_width=2)
        back_from_button_templates = types.InlineKeyboardButton(text='Назад', callback_data='button_clients')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_templates.add(back_from_button_templates, main_menu, row_width=2)
        bot.edit_message_text('Шаблон какого клиента необходимо выгрузить?', call.message.chat.id, call.message.message_id,reply_markup=button_templates)
    ### УРОВЕНЬ 4 "ТЕЛЕ2" 
    elif call.data == "button_tele2":
        bot.send_message(call.message.chat.id, text='Пожалуйста, ожидайте. По завершении процесса, в чат будет отправлен файл отчета.')
        setup_script = 'Скрипт_формирования_отчёта_клиента_Теле2.ps1'
        try:
            result_tele2 = subprocess.run([
                "pwsh", 
                "-File", 
                setup_script,
            ],
            stdout=sys.stdout)
            # Записываем в лог информацию о пользователе, сформировавшем отчет
            with open('data.xml') as f:
                xml_data = f.read()
                root = ET.fromstring(xml_data)
                chat_id = root.find('chat_id').text
                if str(call.message.chat.id) == chat_id:
                    name = root.find('header_footer/name').text
                    logger.info(f"Пользователь {name} сформировал отчет.")
        except subprocess.CalledProcessError as e:
            logger.error("Ошибка при запуске скрипта %s: %s", setup_script, e)
            bot.send_message(call.message.chat.id, text='Произошла ошибка при формировании отчета.')
        else:
            if platform.system() == 'Windows':
                # формируем путь к файлу отчета в директории AppData\Local
                report_path = os.path.join(local_appdata_path, 'Отчёт_клиента_Теле2.docx').replace('\\', '/')
            elif platform.system() == 'Linux':
                report_path = os.path.join(local_appdata_path, 'Отчёт_клиента_Теле2.docx')
            bot.send_document(call.message.chat.id, open(report_path, 'rb'))
    
    ### УРОВЕНЬ 4 "ПСБ"
    elif call.data == "button_psb":  
        bot.send_message(call.message.chat.id, text='Пожалуйста, ожидайте. По завершении процесса, в чат будет отправлен файл отчета.')
        setup_script = 'Скрипт_формирования_отчёта_клиента_ПСБ.ps1'
        result_rez = subprocess.run([
            "pwsh", 
            "-File", 
            setup_script,
          ],
          stdout=sys.stdout)
        bot.send_document(call.message.chat.id, open('C:/Users/Adena/AppData/Local/Отчёт_клиента_ПСБ.docx', 'rb'))       
    ### УРОВЕНЬ 4 "РЭЦ"
    elif call.data == "button_rez":  
        bot.send_message(call.message.chat.id, text='Пожалуйста, ожидайте. По завершении процесса, в чат будет отправлен файл отчета.')
        setup_script = 'Скрипт_формирования_отчёта_клиента_РЭЦ.ps1'
        result_rez = subprocess.run([
            "pwsh", 
            "-File", 
            setup_script,
          ],
          stdout=sys.stdout)
        bot.send_document(call.message.chat.id, open('C:/Users/Adena/AppData/Local/Отчёт_клиента_РЭЦ.docx', 'rb'))      
    ### УРОВЕНЬ 4 "ПОЧТА РОССИИ" ///////////////////////////////////////// в работе
    #elif call.data == "button_pochtaR": 

# УРОВЕНЬ 2 "SD (GOLD & PLATINUM)". Добавляем кнопки [Обновление версии приложения] / [Остальные тикеты]
    elif call.data == "button_SD_Gold_Platinum":
        button_SD_Gold_Platinum = types.InlineKeyboardMarkup()
        button_update_tickets_GP = types.InlineKeyboardButton(text='Обновление версии приложения (G&P)', callback_data='button_update_tickets_GP')
        button_else_GP = types.InlineKeyboardButton(text= 'Остальные тикеты (G&P)', callback_data='button_else_GP')
        button_SD_Gold_Platinum.add(button_update_tickets_GP, button_else_GP, row_width=1)
        back_from_button_SD_Gold_Platinum = types.InlineKeyboardButton(text= 'Назад', callback_data='mainmenu')
        button_SD_Gold_Platinum.add(back_from_button_SD_Gold_Platinum, row_width=1)
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_SD_Gold_Platinum)
    # УРОВЕНЬ 3 "ОБНОВЛЕНИЕ ВЕРСИИ ПРИЛОЖЕНИЯ" (G&P). Добавляем кнопки [Создать тикеты по списку] / [Повторный запрос сервисного окна]
    elif call.data == "button_update_tickets_GP":
        button_update_tickets_GP = types.InlineKeyboardMarkup()
        button_create_tickets_GP = types.InlineKeyboardButton(text='Создать тикеты по списку (G&P)', callback_data='button_create_tickets_GP')
        button_reply_request_GP = types.InlineKeyboardButton(text= 'Повторный запрос сервисного окна (G&P)', callback_data='button_reply_request_GP')
        button_update_tickets_GP.add(button_create_tickets_GP, button_reply_request_GP, row_width=1)
        back_from_button_update_tickets_GP = types.InlineKeyboardButton(text= 'Назад', callback_data='button_SD_Gold_Platinum')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_update_tickets_GP.add(back_from_button_update_tickets_GP, main_menu, row_width=2)
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_update_tickets_GP)
    ### УРОВЕНЬ 4 "СОЗДАТЬ ТИКЕТЫ ПО СПИСКУ" (G&P)
    elif call.data == "button_create_tickets_GP":
        button_create_tickets_GP = types.InlineKeyboardMarkup()
        back_from_button_create_tickets_GP = types.InlineKeyboardButton(text= 'Назад', callback_data='button_update_tickets_GP')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_create_tickets_GP.add(back_from_button_create_tickets_GP, main_menu, row_width=2)
        create = bot.edit_message_text('Пожалуйста, напишите в чат номер версии. Пример: 2.60.', call.message.chat.id, call.message.message_id,reply_markup=button_create_tickets_GP)
        bot.register_next_step_handler(create,send_text_for_create_GP)
    ### УРОВЕНЬ 4 "ПОВТОРНЫЙ ЗАПРОС СЕРВИСНОГО ОКНА" (G&P)
    elif call.data == "button_reply_request_GP":
        button_reply_request_GP = types.InlineKeyboardMarkup()
        button_reply_request_GP_yes = types.InlineKeyboardButton(text= 'Да', callback_data='button_reply_request_GP_yes')
        button_reply_request_GP.add(button_reply_request_GP_yes, row_width=1)
        back_from_button_reply_request_GP = types.InlineKeyboardButton(text= 'Назад', callback_data='button_update_tickets_GP')
        main_menu = types.InlineKeyboardButton(text='Главное меню', callback_data='mainmenu')
        button_reply_request_GP.add(back_from_button_reply_request_GP, main_menu, row_width=2)
        bot.edit_message_text('Вы собираетесь запустить повторную отправку запросов на предоставление сервисного окна для Gold и Platinum клиентов. Подтвердите свой выбор.', call.message.chat.id, call.message.message_id,reply_markup=button_reply_request_GP)
    #### УРОВЕНЬ 5: при нажатии кнопки ДА по повторной отправке запроса сервисного окна для G&P     
    elif call.data == "button_reply_request_GP_yes":
        bot.send_message(call.message.chat.id, text='Процесс запущен, ожидайте.')
        setup_script = 'Auto_ping_test.ps1'
        subprocess.run([
            "pwsh", 
            "-File", 
            setup_script
          ],
          stdout=sys.stdout)
        bot.send_message(call.message.chat.id, text='Процесс завершен. Повторные запросы направлены клиентам.')
    
    # УРОВЕНЬ 3 "ОСТАЛЬНЫЕ ТИКЕТЫ" (G&P) ///////////////////////////////////////////////// в работе
    elif call.data == "button_else_GP":    
        button_else_GP = types.InlineKeyboardMarkup()
        back_from_button_else_GP = types.InlineKeyboardButton(text='Назад', callback_data='button_SD_Gold_Platinum')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_else_GP.add(back_from_button_else_GP, main_menu, row_width=2)
        bot.edit_message_text('Кнопка на ремонте.', call.message.chat.id, call.message.message_id,reply_markup=button_else_GP)
# УРОВЕНЬ 2 "SD (SILVER & BRONZE)". Добавляем кнопки [Обновление версии приложения] / [Остальные тикеты]
    elif call.data == "button_SD_Silver_Bronze":
        button_SD_Silver_Bronze = types.InlineKeyboardMarkup()
        button_update_tickets_SB = types.InlineKeyboardButton(text='Обновление версии приложения (S&B)', callback_data='button_update_tickets_SB')
        button_else_SB = types.InlineKeyboardButton(text= 'Остальные тикеты (S&B)', callback_data='button_else_SB')
        button_SD_Silver_Bronze.add(button_update_tickets_SB, button_else_SB, row_width=1)
        back_from_button_SD_Silver_Bronze = types.InlineKeyboardButton(text= 'Назад', callback_data='mainmenu')
        button_SD_Silver_Bronze.add(back_from_button_SD_Silver_Bronze, row_width=1)
        bot.edit_message_text('Выберите раздел:', call.message.chat.id, call.message.message_id,reply_markup=button_SD_Silver_Bronze)
    # УРОВЕНЬ 3 "ОБНОВЛЕНИЕ ВЕРСИИ ПРИЛОЖЕНИЯ" (S&B). Добавляем кнопки [Создать тикеты по списку] / [Получить статистику по тикетам] 
    elif call.data == "button_update_tickets_SB":
        button_update_tickets_SB = types.InlineKeyboardMarkup()
        button_create_update_tickets_SB = types.InlineKeyboardButton(text='Создать тикеты по списку (S&B)', callback_data='button_create_update_tickets_SB')
        button_update_statistics_SB = types.InlineKeyboardButton(text= 'Получить статистику по тикетам (S&B)', callback_data='button_update_statistics_SB')
        button_update_tickets_SB.add(button_create_update_tickets_SB, button_update_statistics_SB, row_width=1)
        back_from_button_update_tickets_SB = types.InlineKeyboardButton(text= 'Назад', callback_data='button_SD_Silver_Bronze')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_update_tickets_SB.add(back_from_button_update_tickets_SB, main_menu, row_width=2)
        bot.edit_message_text('Какое действие необходимо выполнить?', call.message.chat.id, call.message.message_id,reply_markup=button_update_tickets_SB)
    ### УРОВЕНЬ 4 "СОЗДАТЬ ТИКЕТЫ ПО СПИСКУ" (S&B) [ОБНОВЛЕНИЕ]
    elif call.data == "button_create_update_tickets_SB":
        button_create_update_tickets_SB = types.InlineKeyboardMarkup()
        back_from_button_create_update_tickets_SB = types.InlineKeyboardButton(text= 'Назад', callback_data='button_update_tickets_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_create_update_tickets_SB.add(back_from_button_create_update_tickets_SB, main_menu, row_width=2)
        choice = bot.edit_message_text('Пожалуйста, напишите в чат номер версии. Пример: 2.60.', call.message.chat.id, call.message.message_id,reply_markup=button_create_update_tickets_SB)
        bot.register_next_step_handler(choice,send_text_for_create_SB)

    ### УРОВЕНЬ 4 "ПОЛУЧИТЬ СТАТИСТИКУ ПО ТИКЕТАМ" (S&B) [ОБНОВЛЕНИЕ] 
    elif call.data == "button_update_statistics_SB":
        button_update_statistics_SB = types.InlineKeyboardMarkup()
        back_from_button_update_statistics_SB = types.InlineKeyboardButton(text='Назад', callback_data='button_update_tickets_SB')
        main_menu = types.InlineKeyboardButton(text='Главное меню', callback_data='mainmenu')
        button_update_statistics_SB.add(back_from_button_update_statistics_SB, main_menu, row_width=2)
        choice_stat_version = bot.edit_message_text('Пожалуйста, напишите в чат номер версии, в разрезе которой необходимо сформировать статистику. Пример: 2.60.', call.message.chat.id, call.message.message_id,reply_markup=button_update_statistics_SB)
        bot.register_next_step_handler(choice_stat_version, send_text_for_stat_update_SB)

    # УРОВЕНЬ 3 "ОСТАЛЬНЫЕ ТИКЕТЫ" (S&B) Добавляем кнопки [Получить статистику по тикетам] ///////////////////////////////////////////////// в работе
    elif call.data == "button_else_SB": 
        button_else_SB = types.InlineKeyboardMarkup()
        button_statistics_else_tickets_SB = types.InlineKeyboardButton(text= 'Получить статистику по тикетам', callback_data='button_statistics_else_tickets_SB')
        button_else_SB.add(button_statistics_else_tickets_SB, row_width=1)
        back_from_button_else_SB = types.InlineKeyboardButton(text= 'Назад', callback_data='button_SD_Silver_Bronze')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_else_SB.add(back_from_button_else_SB, main_menu, row_width=2)
        bot.edit_message_text('Какое действие необходимо выполнить?', call.message.chat.id, call.message.message_id,reply_markup=button_else_SB)
    ### УРОВЕНЬ 4 "ПОЛУЧИТЬ СТАТИСТИКУ ПО ТИКЕТАМ" [ОСТАЛЬНЫЕ]  ///////////////////////////////////////////////// в работе
    elif call.data == "button_statistics_else_tickets_SB":
        button_statistics_else_tickets_SB = types.InlineKeyboardMarkup()
        back_from_button_statistics_else_tickets_SB = types.InlineKeyboardButton(text='Назад', callback_data='button_else_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_statistics_else_tickets_SB.add(back_from_button_statistics_else_tickets_SB, main_menu, row_width=2)
        bot.edit_message_text('Кнопка на ремонте.', call.message.chat.id, call.message.message_id,reply_markup=button_statistics_else_tickets_SB)

#### ДОПОЛНИТЕЛЬНО: при нажатии кнопки ДА по корректности темы в рассылке тикетов по обновлению
    ## ДЛЯ SB
    elif call.data == "button_choise_yes_SB":
        bot.edit_message_text('Отлично! Начат процесс создания тикетов и рассылки писем по списку. Пожалуйста, ожидайте.', call.message.chat.id, call.message.message_id)
        setup_script = Path('bot-tg', 'BM_bot', 'Automatic_email_BS.ps1')
        subprocess.run([
            "pwsh", 
            "-File", 
            setup_script,
            str(version_SB) ],
        stdout=sys.stdout)
        button_choise_yes_SB = types.InlineKeyboardMarkup()
        back_from_button_choise_yes_SB = types.InlineKeyboardButton(text='Назад', callback_data='button_create_update_tickets_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_choise_yes_SB.add(back_from_button_choise_yes_SB, main_menu, row_width=2)
        bot.edit_message_text('Процесс завершен. Тикеты созданы, рассылка отправлена. Файл с результатами отправлен на почту.', call.message.chat.id, call.message.message_id,reply_markup=button_choise_yes_SB)
        
    ## ДЛЯ GP
    elif call.data == "button_choise_yes_GP":
        bot.edit_message_text('Отлично! Начат процесс создания тикетов и рассылки писем по списку. Пожалуйста, ожидайте.', call.message.chat.id, call.message.message_id)
        setup_script = Path('bot-tg', 'BM_bot', 'Automatic_email_GP(OLD_TEXT).ps1')
        subprocess.run([
            "pwsh", 
            "-File", 
            setup_script,
            str(version_GP) ],
        stdout=sys.stdout)
        button_choise_yes_GP = types.InlineKeyboardMarkup()
        back_from_button_choise_yes_GP = types.InlineKeyboardButton(text='Назад', callback_data='button_create_tickets_GP')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_choise_yes_GP.add(back_from_button_choise_yes_GP, main_menu, row_width=2)
        bot.edit_message_text('Процесс завершен. Тикеты созданы, рассылка отправлена. Файл с результатами отправлен на почту.', call.message.chat.id, call.message.message_id,reply_markup=button_choise_yes_GP)

#### ДОПОЛНИТЕЛЬНО: при нажатии кнопки ДА по формированию статистики по тикетам SB update
    elif call.data == "button_update_statistics_yes_SB":
        bot.edit_message_text('Отлично! Произвожу расчеты. Пожалуйста, ожидайте.', call.message.chat.id, call.message.message_id)
        setup_script = Path('bot-tg', 'BM_bot', 'Ticket_Check_SB_update_statistics.ps1')
        result=subprocess.run([
            "pwsh", 
            "-File", 
            setup_script,
            str(version_stat)], capture_output=True, text=True
        )
        button_update_statistics_yes_SB = types.InlineKeyboardMarkup()
        back_from_button_update_statistics_yes_SB = types.InlineKeyboardButton(text='Назад', callback_data='button_update_statistics_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_update_statistics_yes_SB.add(back_from_button_update_statistics_yes_SB, main_menu, row_width=2)
        bot.edit_message_text(('Статистика по обновлению версии  "' + str(version_stat) + '" :\n' + str(result.stdout)), call.message.chat.id, call.message.message_id,reply_markup=button_update_statistics_yes_SB)

# УРОВЕНЬ 3 "УЗНАТЬ ВЕРСИЮ КЛИЕНТА" - ФОРМИРОВАНИЕ СПИСКА И ВЫЗОВ ФУНКЦИИ:
@bot.chosen_inline_handler(func=lambda result_client_version: True)
# ФУНКЦИИ К КНОПКЕ ВЕРСИИ КЛИЕНТА
## Функция по созданию списка версий и формирования ответа
def send_text_version(result_client_version):
    bot.add_poll_answer_handler
    url = "https://boardmaps.happyfox.com/api/1.1/json/contact_groups/"
    res = requests.get(url,auth=auth, headers=headers).json()
    global list_info_zero
    list_info_zero = []
    for person in res:
        list_name = person.get('name')
        list_version = person.get('description')
        if '---' in str(list_version):
            continue
        else:
            list_info_zero.append(list_name + ': ' + str(list_version))
    if result_client_version.text.lower() in str(list_info_zero).lower():
        counter = 0
        list = []
        for i in range (len(list_info_zero)):
            if result_client_version.text.lower() in str(list_info_zero[i]).lower():
                counter += 1
                list.append(list_info_zero[i])
        if counter == 1:
            button_version = types.InlineKeyboardMarkup()
            button_version_reply = types.InlineKeyboardButton(text= 'Запросить', callback_data='button_version')
            button_version.add(button_version_reply, row_width=1)
            back_from_result_client_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients_version')
            main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
            button_version.add(back_from_result_client_version, main_menu, row_width=2)
            question = (''.join(map(str, list)) + '\nХотите запросить версию другого клиента?')
            bot.send_message(result_client_version.from_user.id, text=question, reply_markup=button_version) 
        elif counter > 1:
            button_version = types.InlineKeyboardMarkup()
            button_version_reply = types.InlineKeyboardButton(text= 'Запросить', callback_data='button_version')
            button_version.add(button_version_reply, row_width=1)
            back_from_result_client_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients_version')
            main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
            button_version.add(back_from_result_client_version, main_menu, row_width=2)
            question = ('В списке клиентов обнаружено несколько совпадений c запросом "' + result_client_version.text + '":\n' + ('\n'.join(map(str, list))) + '\nХотите запросить версию другого клиента?')
            bot.send_message(result_client_version.from_user.id, text=question, reply_markup=button_version)
    else:
        button_version = types.InlineKeyboardMarkup()
        button_version_reply = types.InlineKeyboardButton(text= 'Запросить', callback_data='button_version')
        button_version.add(button_version_reply, row_width=1)
        back_from_result_client_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients_version')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_version.add(back_from_result_client_version, main_menu, row_width=2)
        question = 'Не найдено совпадений.\nХотите направить запрос ещё раз?'
        bot.send_message(result_client_version.from_user.id, text=question, reply_markup=button_version) 

# ФУНКЦИИ К КНОПКЕ СОЗДАНИЯ ТИКЕТОВ [общ.]
@bot.chosen_inline_handler(func=lambda result_GP_update_version: True)
## Функция по обработке номера версии от пользака (G&P) и подтверждению темы
def send_text_for_create_GP(result_GP_update_version):
    global version_GP
    version_GP = result_GP_update_version.text 
    if '.' in version_GP:
        button_create_tickets_GP = types.InlineKeyboardMarkup()
        button_choise_yes_GP = types.InlineKeyboardButton(text= 'Да', callback_data='button_choise_yes_GP')
        button_create_tickets_GP.add(button_choise_yes_GP, row_width=1)
        back_from_result_GP_update_version= types.InlineKeyboardButton(text= 'Назад', callback_data='button_create_tickets_GP')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_create_tickets_GP.add(back_from_result_GP_update_version, main_menu, row_width=2)
        question = 'Просьба проверить, корректна ли тема будущей рассылки: "Обновление BoardMaps ' + str(version_GP)  + '". \n\n Для запуска процесса формирования тикетов,нажмите "Да". Если тема некорректна, нажмите "Главное меню".'
        bot.send_message(result_GP_update_version.from_user.id, text=question, reply_markup=button_create_tickets_GP)   
    else:
        button_create_tickets_GP = types.InlineKeyboardMarkup()
        back_from_result_GP_update_version= types.InlineKeyboardButton(text= 'Назад', callback_data='button_create_tickets_GP')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_create_tickets_GP.add(back_from_result_GP_update_version, main_menu, row_width=2)
        bot.send_message(result_GP_update_version.from_user.id, text='Запрос не соответствует условиям. Пожалуйста, вернитесь назад и повторите попытку.', reply_markup=button_create_tickets_GP) 

@bot.chosen_inline_handler(func=lambda result_SB_update_version: True) 
## Функция по обработке номера версии от пользака (S&B) и подтверждению темы
def send_text_for_create_SB(result_SB_update_version):
    global version_SB
    version_SB = result_SB_update_version.text
    if '.' in version_SB:
        button_create_update_tickets_SB = types.InlineKeyboardMarkup()
        button_choise_yes_SB = types.InlineKeyboardButton(text= 'Да', callback_data='button_choise_yes_SB')
        button_create_update_tickets_SB.add(button_choise_yes_SB, row_width=1)
        back_from_result_SB_update_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_create_update_tickets_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_create_update_tickets_SB.add(back_from_result_SB_update_version, main_menu, row_width=2)
        question = 'Просьба проверить, корректна ли тема будущей рассылки: "Обновление BoardMaps ' + str(version_SB)  + '". \n\n Для запуска процесса формирования тикетов,нажмите "Да". Если тема некорректна, нажмите "Главное меню".'
        bot.send_message(result_SB_update_version.from_user.id, text=question, reply_markup=button_create_update_tickets_SB) 
    else:
        button_create_update_tickets_SB = types.InlineKeyboardMarkup()
        back_from_result_SB_update_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_create_update_tickets_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_create_update_tickets_SB.add(back_from_result_SB_update_version, main_menu, row_width=2)
        bot.send_message(result_SB_update_version.from_user.id, text='Запрос не соответствует условиям. Пожалуйста, вернитесь назад и повторите попытку.', reply_markup=button_create_update_tickets_SB) 

# ФУНКЦИИ К КНОПКЕ ФОРМИРОВАНИЯ СТАТИСТИКИ []
@bot.chosen_inline_handler(func=lambda result_SB_update_statistic: True) 
## Функция по обработке номера версии от пользака (S&B) и подтверждению темы
def send_text_for_stat_update_SB(result_SB_update_statistic):
    global version_stat
    version_stat = result_SB_update_statistic.text 
    if '.' in version_stat:
        button_update_statistics_SB = types.InlineKeyboardMarkup()
        button_update_statistics_yes_SB = types.InlineKeyboardButton(text= 'Да', callback_data='button_update_statistics_yes_SB')
        button_update_statistics_SB.add(button_update_statistics_yes_SB, row_width=1)
        back_from_result_SB_update_statistic = types.InlineKeyboardButton(text= 'Назад', callback_data='button_update_statistics_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_update_statistics_SB.add(back_from_result_SB_update_statistic, main_menu, row_width=2)
        question = 'Формируем статистику по версии релиза "' + str(version_stat)  + '"?'
        bot.send_message(result_SB_update_statistic.from_user.id, text=question, reply_markup=button_update_statistics_SB) 
    else:
        button_update_statistics_SB = types.InlineKeyboardMarkup()
        back_from_result_SB_update_statistic = types.InlineKeyboardButton(text= 'Назад', callback_data='button_update_statistics_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_update_statistics_SB.add(back_from_result_SB_update_statistic, main_menu, row_width=2)
        bot.send_message(result_SB_update_statistic.from_user.id, text='Запрос не соответствует условиям. Пожалуйста, вернитесь назад и повторите попытку.', reply_markup=button_update_statistics_SB) 
   

def start_telegram_bot():
    """"Функция запуска телебота"""
    # запуск бота
    bot.infinity_polling()
