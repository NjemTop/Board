from telebot import types

class ButtonUpdate():
    def button_SD_update():
        """ УРОВЕНЬ 2: ОБНОВЛЕНИЕ ВЕРСИИ. Добавляем кнопки [ Отправить рассылку | Локализация | Повторный запрос сервисного окна (G&P) | Статистика по тикетам ] """
        button_SD_update = types.InlineKeyboardMarkup()
        button_release = types.InlineKeyboardButton(text='Отправить рассылку', callback_data='button_release')
        button_localizable = types.InlineKeyboardButton(text='Локализация', callback_data='button_localizable')
        button_reply_request = types.InlineKeyboardButton(text='Повторный запрос сервисного окна (G&P)', callback_data='button_reply_request')
        button_update_statistics = types.InlineKeyboardButton(text='Статистика по тикетам', callback_data='button_update_statistics')
        back_from_mainmenu = types.InlineKeyboardButton(text= 'Назад', callback_data='mainmenu')
        button_SD_update.add(button_release, button_localizable, button_reply_request, button_update_statistics, back_from_mainmenu, row_width=1)
        return button_SD_update
    def button_release():
        """переход к вопросу "напишите номер версии". и дальше по списку"""
        button_release = types.InlineKeyboardMarkup()
        button_release_cancel = types.InlineKeyboardButton(text= 'Отмена', callback_data='cancel_SD_update')
        button_release.add(button_release_cancel, row_width=1)
        return button_release
    def correct_version_release(version_release):
        button_release = types.InlineKeyboardMarkup()
        button_choise_yes = types.InlineKeyboardButton(text= 'Да', callback_data='button_choise_yes')
        button_release.add(button_choise_yes, row_width=1)
        back_from_result_update_version= types.InlineKeyboardButton(text= 'Назад', callback_data='button_release')
        main_menu = types.InlineKeyboardButton(text= 'Главное меню', callback_data='mainmenu')
        button_release.add(back_from_result_update_version, main_menu, row_width=2)
        question = 'Просьба проверить, корректна ли тема будущей рассылки: "Обновление BoardMaps ' + str(version_release)  + '". \n\n Для запуска процесса формирования тикетов,нажмите "Да". Если тема некорректна, нажмите "Главное меню".'
        return button_release, question

    def button_localizable():
        """переход к списку клиентов для создания файла локализации"""
        button_localizable = types.InlineKeyboardMarkup()
        button_AFK = types.InlineKeyboardButton(text='АФК', callback_data='button_AFK')
        button_GPB = types.InlineKeyboardButton(text='ГПБ', callback_data='button_GPB')
        button_Alfa = types.InlineKeyboardButton(text='Альфа-Банк', callback_data='button_Alfa')
        button_IBS = types.InlineKeyboardButton(text='IBS', callback_data='button_IBS')
        localizable_button = types.InlineKeyboardButton(text='Локализация', callback_data='button_localizable')
        button_localizable.add(button_AFK, button_GPB, button_Alfa, button_IBS, localizable_button, row_width=2)
        back_from_button_SD_update = types.InlineKeyboardButton(text= 'Назад', callback_data='button_SD_update')
        button_localizable.add(back_from_button_SD_update, row_width=2)
        return button_localizable

    def button_AFK_localizable():
        button_AFK_localizable = types.InlineKeyboardMarkup()
        button_AFK_loc_IPad = types.InlineKeyboardButton(text= 'Локализация для iPad', callback_data='button_AFK_loc_IPad')
        button_AFK_loc_Web = types.InlineKeyboardButton(text= 'Локализация для Web', callback_data='button_AFK_loc_Web')
        button_AFK_localizable.add(button_AFK_loc_IPad, button_AFK_loc_Web, row_width=1)
        back_from_button_AFK_loc = types.InlineKeyboardButton(text= 'Назад', callback_data='button_localizable')
        button_AFK_localizable.add(back_from_button_AFK_loc, row_width=1)
        return button_AFK_localizable
    def button_GPB_localizable():
        button_GPB_localizable = types.InlineKeyboardMarkup()
        button_GPB_loc_IPad = types.InlineKeyboardButton(text= 'Локализация для iPad', callback_data='button_GPB_loc_IPad')
        button_GPB_loc_Web = types.InlineKeyboardButton(text= 'Локализация для Web', callback_data='button_GPB_loc_Web')
        button_GPB_localizable.add(button_GPB_loc_IPad, button_GPB_loc_Web, row_width=1)
        back_from_button_GPB_loc = types.InlineKeyboardButton(text= 'Назад', callback_data='button_localizable')
        button_GPB_localizable.add(back_from_button_GPB_loc, row_width=1)
        return button_GPB_localizable
    def button_Alfa_localizable():
        button_Alfa_localizable = types.InlineKeyboardMarkup()
        button_Alfa_loc_IPad = types.InlineKeyboardButton(text= 'Локализация для iPad', callback_data='button_Alfa_loc_IPad')
        button_Alfa_loc_Web = types.InlineKeyboardButton(text= 'Локализация для Web', callback_data='button_Alfa_loc_Web')
        button_Alfa_localizable.add(button_Alfa_loc_IPad, button_Alfa_loc_Web, row_width=1)
        back_from_button_Alfa_loc = types.InlineKeyboardButton(text= 'Назад', callback_data='button_localizable')
        button_Alfa_localizable.add(back_from_button_Alfa_loc, row_width=1)
        return button_Alfa_localizable
    def button_IBS_localizable():
        button_IBS_localizable = types.InlineKeyboardMarkup()
        button_IBS_loc_IPad = types.InlineKeyboardButton(text= 'Локализация для iPad', callback_data='button_IBS_loc_IPad')
        button_IBS_loc_Web = types.InlineKeyboardButton(text= 'Локализация для Web', callback_data='button_IBS_loc_Web')
        button_IBS_localizable.add(button_IBS_loc_IPad, button_IBS_loc_Web, row_width=1)
        back_from_button_IBS_loc = types.InlineKeyboardButton(text= 'Назад', callback_data='button_localizable')
        button_IBS_localizable.add(back_from_button_IBS_loc, row_width=1)
        return button_IBS_localizable
    
    def button_reply_request():
        """переход к вопросу "Вы собираетесь запустить повторную отправку запросов. и дальше по списку"""
        button_reply_request = types.InlineKeyboardMarkup()
        button_reply_request_yes = types.InlineKeyboardButton(text= 'Да', callback_data='button_reply_request_yes')
        button_reply_request_cancel = types.InlineKeyboardButton(text= 'Отмена', callback_data='button_SD_update')
        button_reply_request.add(button_reply_request_yes, button_reply_request_cancel, row_width=1)
        return button_reply_request
    def button_update_statistics(version_stat):
        button_update_statistics = types.InlineKeyboardMarkup()
        button_update_statistics_yes = types.InlineKeyboardButton(text= 'Да', callback_data='button_update_statistics_yes')
        button_update_statistics_cancel = types.InlineKeyboardButton(text= 'Отмена', callback_data='button_SD_update')
        button_update_statistics.add(button_update_statistics_yes, button_update_statistics_cancel, row_width=1)
        question = 'Формируем статистику по версии релиза "' + str(version_stat)  + '"?'
        return button_update_statistics, question
    