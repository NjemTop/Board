import logging
from logging.handlers import RotatingFileHandler
import os

def get_abs_log_path(log_filename):
    # Получаем абсолютный путь до файла с настройками логгера (log_config.py)
    log_config_path = os.path.abspath(os.path.dirname(__file__))
    # Получаем абсолютный путь до корневой папки проекта
    project_root = os.path.dirname(log_config_path)
    # Формируем абсолютный путь до папки logs и файла с логами
    log_file_path = os.path.join(project_root, 'logs', log_filename)
    return log_file_path


def setup_logger(logger_name, log_file, level=logging.INFO, max_size=10, backup_count=10):
    logger = logging.getLogger(logger_name)

    if not logger.hasHandlers():
        logger.setLevel(level)

        # Создаем папку logs, если её еще нет
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Создаем файл с логами, если еще не существует
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                pass

        handler = RotatingFileHandler(log_file, maxBytes=max_size*1024*1024, backupCount=backup_count)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
