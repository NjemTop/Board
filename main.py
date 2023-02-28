import multiprocessing
from web_server import run_server
from telegram_bot import start_telegram_bot

if __name__ == '__main__':
    try:
        web_server_process = multiprocessing.Process(target=run_server)
        web_server_process.start()
        start_telegram_bot() # Добавляем запуск телебота
    except Exception as e:
        print("Ошибка при запуске сервера:", e)
