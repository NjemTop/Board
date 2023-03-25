from telebot import types

class ButtonClients():
    def button_clients():
        """ УРОВЕНЬ 2 "КЛИЕНТЫ". Добавляем кнопки [Список клиентов] / [Версии клиентов] / [Шаблоны] """
        button_clients = types.InlineKeyboardMarkup()
        button_list_of_clients = types.InlineKeyboardButton(text='Список клиентов', callback_data='button_list_of_clients')
        button_clients_version = types.InlineKeyboardButton(text='Версии клиентов', callback_data='button_clients_version')
        button_templates = types.InlineKeyboardButton(text='Статистика по тикетам за период (шаблоны)', callback_data='button_templates')
        button_clients.add(button_list_of_clients, button_clients_version, button_templates, row_width=2)
        back_from_button_clients = types.InlineKeyboardButton(text='Назад', callback_data='mainmenu')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_clients.add(back_from_button_clients, main_menu, row_width=2)
        return button_clients
    def button_list_of_clients():
        """ УРОВЕНЬ 3. Вызов кнопки "СПИСОК КЛИЕНТОВ" """
        button_list_of_clients = types.InlineKeyboardMarkup()
        back_from_button_list_of_clients = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_list_of_clients.add(back_from_button_list_of_clients, main_menu, row_width=2)
        return button_list_of_clients
    def button_clients_version():
        """ УРОВЕНЬ 3 "ВЕРСИИ КЛИЕНТОВ". Добавляем кнопки [Общий список версий] / [Узнать версию клиента] """
        button_clients_version = types.InlineKeyboardMarkup()
        button_version_main_list = types.InlineKeyboardButton(text='Общий список версий', callback_data='button_version_main_list')
        button_version = types.InlineKeyboardButton(text= 'Узнать версию клиента', callback_data='button_version')
        button_clients_version.add(button_version_main_list, button_version, row_width=2)
        back_from_button_clients_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_clients_version.add(back_from_button_clients_version, main_menu, row_width=2)
        return button_clients_version
    def button_version_main_list():
        """ УРОВЕНЬ 4 "ОБЩИЙ СПИСОК ВЕРСИЙ". Добавляем ссылку на список """
        button_version_main_list = types.InlineKeyboardMarkup()
        back_from_button_version_main_list = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients_version')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_version_main_list.add(back_from_button_version_main_list, main_menu, row_width=2)
        return button_version_main_list
    def button_version():
        """ УРОВЕНЬ 4 "УЗНАТЬ ВЕРСИЮ КЛИЕНТА" """
        button_version = types.InlineKeyboardMarkup()
        back_from_button_version = types.InlineKeyboardButton(text='Отмена', callback_data='cancel_button_version') 
        main_menu = types.InlineKeyboardButton(text='Главное меню', callback_data='mainmenu')
        button_version.add(back_from_button_version, main_menu, row_width=2)
        return button_version
    def button_templates():
        """ УРОВЕНЬ 3 "ШАБЛОНЫ". Добавляем кнопки [Теле2] / [ПСБ] / [РЭЦ] / [Почта России] """
        button_templates = types.InlineKeyboardMarkup()
        button_tele2 = types.InlineKeyboardButton(text='Теле2', callback_data='button_tele2')
        button_psb = types.InlineKeyboardButton(text='ПСБ', callback_data='button_psb')
        button_rez = types.InlineKeyboardButton(text='РЭЦ', callback_data='button_rez')
        button_pochtaR = types.InlineKeyboardButton(text='Почта России', callback_data='button_pochtaR')
        button_templates.add(button_tele2, button_psb, button_rez, button_pochtaR, row_width=2)
        back_from_button_templates = types.InlineKeyboardButton(text='Назад', callback_data='button_clients')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_templates.add(back_from_button_templates, main_menu, row_width=2)
        return button_templates

    def button_version_answer():
        """Функция по созданию списка версий и формирования ответа"""
        button_version = types.InlineKeyboardMarkup()
        button_version_reply = types.InlineKeyboardButton(text= 'Запросить', callback_data='button_version')
        button_version.add(button_version_reply, row_width=1)
        back_from_result_client_version = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients_version')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_version.add(back_from_result_client_version, main_menu, row_width=2)
        return button_version
