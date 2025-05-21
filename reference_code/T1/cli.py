"""
cli.py - Command-line interface and user interaction for Zoom DNC Genie
"""
from utils.logging_utils import log_info, log_error

def prompt_phone_number() -> str:
    """Prompt user for a 10-digit phone number."""
    while True:
        phone = input("Enter a 10-digit phone number (numbers only): ").strip()
        if phone.isdigit() and len(phone) == 10:
            return phone
        log_error("Invalid input. Please enter exactly 10 digits (no spaces or symbols).")
