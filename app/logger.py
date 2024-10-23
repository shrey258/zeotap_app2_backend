import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')

    handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Ensure log directory exists
os.makedirs('logs', exist_ok=True)

# Create loggers
main_logger = setup_logger('main', 'logs/main.log')
api_logger = setup_logger('api', 'logs/api.log')
weather_logger = setup_logger('weather', 'logs/weather.log')

