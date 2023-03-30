import logging
import os

def get_abs_log_path(log_filename):
    # Получаем абсолютный путь до файла с настройками логгера (log_config.py)
    log_config_path = os.path.abspath(os.path.dirname(__file__))
    # Получаем абсолютный путь до корневой папки проекта
    project_root = os.path.dirname(log_config_path)
    # Формируем абсолютный путь до папки logs и файла с логами
    log_file_path = os.path.join(project_root, 'logs', log_filename)
    return log_file_path

def setup_logger(name, log_file, level=logging.INFO, formatter=None):
    if formatter is None:
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
