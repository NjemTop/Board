import logging
import os

def get_abs_log_path(log_file):
    """Функция для определения места записи логов"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', log_file))

def setup_logger(name, log_file, level=logging.INFO, formatter=None):
    if formatter is None:
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M')

    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
