import multiprocessing
from web_server import run_server

if __name__ == '__main__':
    try:
        web_server_process = multiprocessing.Process(target=run_server)
        web_server_process.start()
    except Exception as e:
        print("Ошибка при запуске сервера:", e)
