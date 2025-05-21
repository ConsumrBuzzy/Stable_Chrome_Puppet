"""
Helper functions for DNC automation.
"""
import logging
from typing import Optional

def validate_phone_number(phone: str) -> bool:
    """
    Validate that the input is a 10-digit number.
    
    Args:
        phone: The phone number string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone.isdigit():
        logging.warning(f"Non-numeric input detected: {phone}")
        return False
    if len(phone) != 10:
        logging.warning(f"Invalid phone number length: {len(phone)} digits")
        return False
    return True

def prompt_phone_number() -> str:
    """
    Prompt user for a 10-digit phone number with validation.
    
    Returns:
        str: Validated 10-digit phone number
    """
    while True:
        try:
            phone = input("Enter 10-digit phone number (digits only): ").strip()
            if validate_phone_number(phone):
                logging.info(f"Valid phone number entered: {phone}")
                return phone
            print("Invalid input. Please enter exactly 10 digits (no spaces or symbols).")
        except KeyboardInterrupt:
            logging.info("Phone number input cancelled by user")
            raise
        except Exception as e:
            logging.error(f"Error processing phone number input: {e}")
            print("An error occurred. Please try again.")
