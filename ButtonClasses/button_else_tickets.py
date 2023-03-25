from telebot import types

class ButtonElseTickets():
    def button_else_GP():
        # УРОВЕНЬ 3 "ОСТАЛЬНЫЕ ТИКЕТЫ" (G&P) 
        button_else_GP = types.InlineKeyboardMarkup()
        back_from_button_else_GP = types.InlineKeyboardButton(text='Назад', callback_data='button_SD_Gold_Platinum')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_else_GP.add(back_from_button_else_GP, main_menu, row_width=2)
        return button_else_GP
    def button_else_SB():
    # УРОВЕНЬ 3 "ОСТАЛЬНЫЕ ТИКЕТЫ" (S&B) Добавляем кнопки [Получить статистику по тикетам] 
        button_else_SB = types.InlineKeyboardMarkup()
        button_statistics_else_tickets_SB = types.InlineKeyboardButton(text= 'Получить статистику по тикетам', callback_data='button_statistics_else_tickets_SB')
        button_else_SB.add(button_statistics_else_tickets_SB, row_width=1)
        back_from_button_else_SB = types.InlineKeyboardButton(text= 'Назад', callback_data='button_SD_Silver_Bronze')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_else_SB.add(back_from_button_else_SB, main_menu, row_width=2)
        return button_else_SB
    def button_statistics_else_tickets_SB():
        button_statistics_else_tickets_SB = types.InlineKeyboardMarkup()
        back_from_button_statistics_else_tickets_SB = types.InlineKeyboardButton(text='Назад', callback_data='button_else_SB')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_statistics_else_tickets_SB.add(back_from_button_statistics_else_tickets_SB, main_menu, row_width=2)
        return button_statistics_else_tickets_SB
    
    