"""
Logging setup and helpers for DNC automation.
Provides info, warning, error, and debug log functions.
@see docs/design_doc.md#12-api-and-interface-specifications
@see docs/reference.md#logging_utils
"""
import logging
import os

LOG_FILE_PATH = "logs/dnc_automation.log"


def setup_logging():
    """
    Sets up logging to both file and console.
    Creates the logs directory if it doesn't exist.
    """
    if not os.path.exists("logs"):
        os.makedirs("logs")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
        ]
    )


def log_info(msg):
    """Log an info-level message."""
    logging.info(msg)


def log_warning(msg):
    """Log a warning-level message."""
    logging.warning(msg)


def log_error(msg):
    """Log an error-level message."""
    logging.error(msg)


def log_debug(msg):
    """Log a debug-level message."""
    logging.debug(msg)

