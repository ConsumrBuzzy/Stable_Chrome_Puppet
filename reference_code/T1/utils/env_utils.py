"""
env_utils.py
Utility functions for environment variable and credential loading for Zoom DNC Genie.
"""
import os
import sys
from dotenv import load_dotenv
from colorama import Fore, Style

def load_credentials():
    """Load Zoom credentials from .env file and validate. Refactored for parity with ZoomDNCGenie.py."""
    load_dotenv()
    email = os.getenv("ZOOM_EMAIL")
    password = os.getenv("ZOOM_PASSWORD")
    missing = []
    if not email:
        missing.append("ZOOM_EMAIL")
    if not password:
        missing.append("ZOOM_PASSWORD")
    if missing:
        print(Fore.RED + f"Missing required environment variables: {', '.join(missing)}.\nPlease set them in your .env file." + Style.RESET_ALL)
        import logging
        logging.error(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    return email, password

