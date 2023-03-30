from HappyFox.happyfox_connector import get_happyfox_credentials, get_filtered_tickets

### Авторизация в HappyFox
# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"
# Определяем все важные данные для запросов
API_ENDPOINT, API_KEY, API_SECRET, HEADERS = get_happyfox_credentials(CONFIG_FILE)

contact_group_id = 9
start_date = "2023-03-09"
end_date = "2023-03-31"

filtered_tickets = get_filtered_tickets(API_ENDPOINT, API_KEY, API_SECRET, HEADERS, contact_group_id, start_date, end_date)

for ticket in filtered_tickets:
    ticket_id = ticket['display_id']
    subject = ticket['subject']
    last_modified = ticket['last_updated_at']
    print(f"Ticket {ticket_id}: {subject} (last modified on {last_modified})")
