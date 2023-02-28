import multiprocessing
import os
import threading
import subprocess
from telegram_bot import start_telegram_bot

# Функция запуска ВЕБ-СЕРВЕРА для прослушивания вебхуков. Алерты.
def start_socket_server():
    """Функция запуска ВЭБ-СЕРВЕРА в паралельной сессии"""
    script_path = os.path.abspath(os.path.dirname(__file__))
    subprocess.Popen(['python', os.path.join(script_path, 'socket_server.py')])

# запуск двух функций (запуск скрипта ВЭБ-СЕРВЕРА и запуск скрипта телебота)
if __name__ == '__main__':
    p1 = multiprocessing.Process(target=start_socket_server)
    # Здесь мы используем threading.Thread для запуска функции start_telegram_bot в отдельном потоке, который не блокирует выполнение остального кода.
    p2 = threading.Thread(target=start_telegram_bot)
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    p2.join()
