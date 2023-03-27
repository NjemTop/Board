from telebot import types

class ButtonElseTickets():
    def get_info_else_tickets():
        button_else_tickets = types.InlineKeyboardMarkup(row_width=1)
        button_else_tickets_stat = types.InlineKeyboardButton(text='Общая статистика', callback_data='button_else_tickets_stat')
        button_one_ticket_stat = types.InlineKeyboardButton(text='Просмотр данных отдельного тикета', callback_data='button_one_ticket_stat')
        main_menu = types.InlineKeyboardButton(text='Главное меню', callback_data='mainmenu')
        button_else_tickets.add(button_else_tickets_stat, button_one_ticket_stat, main_menu)
        return button_else_tickets

    def get_info_else_tickets_stat():
        back_from_button_else_tickets_stat = types.InlineKeyboardButton(text='Назад', callback_data='button_else_tickets')
        main_menu = types.InlineKeyboardButton(text='Главное меню', callback_data='mainmenu')
        all_ticket_count = '6'
        new_ticket = '2'
        without_support_answer = '3'
        without_client_answer = '1'
        button_else_tickets_stat = types.InlineKeyboardMarkup(row_width=2)
        button_else_tickets_stat.add(
            types.InlineKeyboardButton(text='Общее количество тикетов: {}'.format(all_ticket_count), callback_data='dummy'),
            types.InlineKeyboardButton(text='Новых тикетов: {}'.format(new_ticket), callback_data='dummy'),
            types.InlineKeyboardButton(text='Без ответа от поддержки: {}'.format(without_support_answer), callback_data='dummy'),
            types.InlineKeyboardButton(text='Без ответа от клиента: {}'.format(without_client_answer), callback_data='dummy')
        )
        button_else_tickets_stat.add(back_from_button_else_tickets_stat, main_menu)
        return button_else_tickets_stat, all_ticket_count, new_ticket, without_support_answer, without_client_answer

    def get_info_one_ticket_stat():
        button_one_ticket_cancel = types.InlineKeyboardButton(text='Отмена', callback_data='cancel_else_tickets')
        button_one_ticket_stat = types.InlineKeyboardMarkup(row_width=1)
        button_one_ticket_stat.add(button_one_ticket_cancel)
        return button_one_ticket_stat
