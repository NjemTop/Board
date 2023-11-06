import requests
import json
import emoji
from urllib.parse import quote

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"

# Читаем данные из файла
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    DATA = json.load(file)

# Получаем значение ключа BOT_TOKEN в TELEGRAM_SETTINGS
BOT_TOKEN = DATA['TELEGRAM_SETTINGS']['BOT_TOKEN']

def send_telegram_message(alert_chat_id, alert_text):
    """
    Отправляет сообщение в телеграм-бот.
    На себя принимает два аргумента:
    alert_chat_id - чат айди, куда мы будем отправлять сообщение,
    alert_text - текст сообщения, которое мы хотим отправить.
    """
    # Адрес для отправи сообщение напрямую через API Telegram
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    # Задаём стандартный заголовок отправки
    headers_server = {'Content-type': 'application/json'}
    # Создаём тело запроса, которое мы отправляем
    data = {
        'chat_id': alert_chat_id,
        'text': f'{alert_text}',
        'parse_mode': 'HTML'
    }
    # Отправляем запрос через наш бот
    response = requests.post(url, headers=headers_server, data=json.dumps(data), timeout=30)
    # Добавляем логгирование для отладки
    print(response)


ticket_id = "BCS00006280"
subject = 'Просим оказать содействие с установкой сертификата.'
client_name = 'Дмитрий Попов'
priority_name = 'Medium'
assignee_name = 'Oleg Eliseev'
client_email = 'Email'
display_id = '#BCS00006630'
agent_ticket_url = 'https://boardmaps.happyfox.com/staff/ticket/6280'
ping_ticket_message = (
    f"{emoji.emojize(':red_exclamation_mark:')} Тикет "
    f'<a href="{agent_ticket_url}">{display_id}</a> '
    f'<b>час</b> без ответа.\n'
    f"{emoji.emojize(':man_tipping_hand:')}Тема: {subject}\n"
    f"{emoji.emojize(':man_mechanic:')}Автор: {client_name}\n"
    f"{emoji.emojize(':high_voltage:')}Приоритет: {priority_name}\n"
    f"{emoji.emojize(':clown_face:')} Назначен: {assignee_name}\n"
)

ticket_message = (
    f"{emoji.emojize(':hand_with_fingers_splayed:')}Новое сообщение в тикете "
    f'<a href="{agent_ticket_url}">{display_id}</a>.\n'
    f"{emoji.emojize(':man_tipping_hand:')}Тема: {subject}\n"
    f"{emoji.emojize(':man_mechanic:')}Автор: {client_name}\n"
    f"{emoji.emojize(':high_voltage:')}Приоритет: {priority_name}\n"
    f"{emoji.emojize(':man_technologist:')}Назначен: {assignee_name}\n"
)

new_ticket_message = (
    f"{emoji.emojize(':tired_face:')}Новый тикет: "
    f"[{ticket_id}]({agent_ticket_url})\n"
    f"{emoji.emojize(':man_tipping_hand:')}Тема: {subject}\n"
    f"{emoji.emojize(':man_mechanic:')}Автор: {client_name} ({client_email})\n"
    f"{emoji.emojize(':high_voltage:')}Приоритет: {priority_name}\n"
)

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"

# Читаем данные из файла
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    DATA = json.load(file)

alert_chat_id = DATA['SEND_ALERT']['GROUP_RELEASE']

print(alert_chat_id)

version_release = 2.68

alert_message_for_release = (
    f"{emoji.emojize(':check_mark_button:')} "
    f"{emoji.emojize(':check_mark_button:')} "
    f"{emoji.emojize(':check_mark_button:')}\n\n"
    f"Рассылка о релизе версии <b>BM {version_release}</b> успешно отправлена!\n\n"
    f"Отчёт по рассылке можно посмотреть "
    f'<a href="https://creg.boardmaps.ru/release_info/">здесь</a>.\n\n'
    f"Всем спасибо!"
)
send_telegram_message(alert_chat_id, alert_message_for_release)
