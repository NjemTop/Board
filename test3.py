from HappyFox.happyfox_class import HappyFoxConnector

config_file = "Main.config"
start_date = "2023-02-12"
end_date = "2023-05-1"
contact_group_id = 37
# 21 (psb), 37 (tele2)
connector = HappyFoxConnector(config_file)
filtered_tickets = connector.get_filtered_tickets(start_date, end_date, contact_group_id)

for ticket in filtered_tickets:
    ticket_id = ticket['display_id']
    subject = ticket['subject']
    last_modified = ticket['last_updated_at']
    print(f"Тикет {ticket_id}: {subject} (Последнее изменение: {last_modified})")