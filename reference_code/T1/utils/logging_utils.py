import logging
import sys
from colorama import Fore, Style, init as colorama_init
import os

colorama_init(autoreset=True)

from datetime import datetime

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Use the actual current time for this session
SESSION_TIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

LOG_FILES = {
    'INFO': os.path.join(LOGS_DIR, f'info_{SESSION_TIME}.log'),
    'WARNING': os.path.join(LOGS_DIR, f'warning_{SESSION_TIME}.log'),
    'ERROR': os.path.join(LOGS_DIR, f'error_{SESSION_TIME}.log'),
    'DEBUG': os.path.join(LOGS_DIR, f'debug_{SESSION_TIME}.log'),
}

class LevelFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = level
    def filter(self, record):
        return record.levelno == self.level

logger = logging.getLogger('dnc_genie')
logger.setLevel(logging.DEBUG)
logger.handlers.clear()

# File handlers for each level
for level_name, log_path in LOG_FILES.items():
    level = getattr(logging, level_name)
    fh = logging.FileHandler(log_path, encoding='utf-8')
    fh.setLevel(level)
    fh.addFilter(LevelFilter(level))
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

# Colorized console handler (all levels)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.CYAN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }
    def format(self, record):
        color = self.COLORS.get(record.levelno, '')
        message = super().format(record)
        return color + message + Style.RESET_ALL
ch.setFormatter(ColorFormatter('%(message)s'))
logger.addHandler(ch)

import os
import logging

# Always use the top-level /logs directory relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, 'dnc_genie.log')

# Configure the logger if not already configured
logger = logging.getLogger('dnc_genie')
if not logger.handlers:
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

def get_logger():
    return logger

def log_info(msg):
    logger.info(msg)

def log_warning(msg):
    logger.warning(msg)

def log_error(msg):
    logger.error(msg)

def log_debug(msg):
    logger.debug(msg)
