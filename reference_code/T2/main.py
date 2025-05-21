"""
main.py
Entry point for the DNC Genie v2 system.

Implements the top-level CLI, credential loading, logging, browser automation,
login, and DNC actions for both DNC systems within the Zoom Admin Portal.
This script is modular and ready for future extension.
"""

import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

from config import settings, setup_logging
from exceptions import (
    handle_error,
    DNCOperationError,
    BrowserError,
    AuthenticationError
)
from rate_limiter import rate_limited, RateLimitContext
from session import session
from auth import zoom_login
from utils import prompt_phone_number
from browser_utils import create_driver
from dnc_workplace import add_to_workplace_dnc
from dnc_contact_center import add_to_contact_center_dncd

# Initialize logging
logger = setup_logging()

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format."""
    return phone.isdigit() and len(phone) == 10

def process_dnc_operations(driver, phone_number: str) -> bool:
    """Process DNC operations with rate limiting and error handling."""
    if not validate_phone_number(phone_number):
        logger.error(f"Invalid phone number format: {phone_number}")
        return False
        
    try:
        # Process Workplace DNC
        logger.info(f"Adding {phone_number} to Workplace DNC list...")
        with RateLimitContext("workplace_dnc"):
            add_to_workplace_dnc(driver, phone_number)
        
        # Process Contact Center DNC
        logger.info(f"Adding {phone_number} to Contact Center DNC list...")
        with RateLimitContext("contact_center_dnc"):
            add_to_contact_center_dnc(driver, phone_number)
            
        return True
        
    except DNCOperationError as e:
        logger.error(f"DNC operation failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

def main():
    """Main entry point for the DNC Genie application."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize WebDriver
        driver = create_driver()
        
        try:
            # Authenticate
            logger.info("Authenticating with Zoom...")
            zoom_login(driver, settings.ZOOM_EMAIL, settings.ZOOM_PASSWORD)
            logger.info("Successfully authenticated with Zoom")
            
            # Main loop
            while True:
                # Prompt for phone number
                phone_number = prompt_phone_number()
                if not phone_number:
                    break
                    
                # Process DNC operations
                success = process_dnc_operations(driver, phone_number)
                if success:
                    logger.info(f"Successfully added {phone_number} to DNC lists")
                else:
                    logger.error(f"Failed to add {phone_number} to DNC lists")
                    
        except AuthenticationError as e:
            logger.error(f"Authentication failed: {str(e)}")
            return 1
        except BrowserError as e:
            logger.error(f"Browser error: {str(e)}")
            return 1
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return 1
        finally:
            # Clean up
            if driver:
                driver.quit()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
