from telebot import types

class ButtonClients():
    # УРОВЕНЬ 2 "КЛИЕНТЫ". Добавляем кнопки [Список клиентов] / [Версии клиентов] / [Шаблоны]
    def button_clients():
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
        button_list_of_clients = types.InlineKeyboardMarkup()
        back_from_button_list_of_clients = types.InlineKeyboardButton(text= 'Назад', callback_data='button_clients')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_list_of_clients.add(back_from_button_list_of_clients, main_menu, row_width=2)
        return button_list_of_clients
