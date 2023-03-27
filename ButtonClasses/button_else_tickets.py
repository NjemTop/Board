from telebot import types

class ButtonElseTickets():
    def get_info_else_tickets():
        button_else_tickets = types.InlineKeyboardButton
        button_else_tickets_stat = types.InlineKeyboardMarkup(text='Общая статистика', callback_data='button_else_tickets_stat')
        button_one_ticket_stat = types.InlineKeyboardMarkup(text='Просмотр данных отдельного тикета', callback_data='button_one_ticket_stat')
        main_menu = types.InlineKeyboardButton(text='Главное меню', callback_data='mainmenu')
        button_else_tickets.add(button_else_tickets_stat, button_one_ticket_stat, main_menu, row_width=1)
        return button_else_tickets
    def get_info_else_tickets_stat():    
        button_else_tickets_stat = types.InlineKeyboardButton
        back_from_button_else_tickets_stat = types.InlineKeyboardButton(text='Назад', callback_data='button_else_tickets')
        main_menu = types.InlineKeyboardButton(text='Главное меню', callback_data='mainmenu')
        button_else_tickets_stat.add(back_from_button_else_tickets_stat, main_menu, row_width=2)
        all_ticket_count = '6'
        new_ticket = '2'
        without_support_answer = '3'
        without_client_ansrew = '1'
        return button_else_tickets_stat, all_ticket_count, new_ticket, without_support_answer, without_client_ansrew
    def get_info_one_ticket_stat():    
        button_one_ticket_stat = types.InlineKeyboardButton
        button_one_ticket_cancel = types.InlineKeyboardButton(text='Отмена', callback_data='cancel_else_tickets')
        button_one_ticket_stat.add(button_one_ticket_cancel, row_width=1)
        return button_one_ticket_stat