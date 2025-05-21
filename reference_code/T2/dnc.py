"""
Contains logic to add phone number to DNC list.
Enhanced error handling and logging per design plan.
@see docs/design_doc.md#12-api-and-interface-specifications
@see docs/reference.md#dnc
"""
from config import DNC_MANAGEMENT_URL, DEFAULT_WAIT
from selenium.webdriver.common.by import By
from utils.logging_utils import log_info, log_error
from utils.exceptions import DNCError  # Centralized custom exception
from utils.selenium_utils import wait_for_element, safe_click, wait_and_fill
# @see docs/design_doc.md, reference/legacy_code/T1/utils/exceptions.py, reference/legacy_code/T1/utils/selenium_utils.py
import time

class DNCError(Exception):
    """Custom exception for DNC add failures."""
    pass

def add_to_dnc(driver, phone_number):
    """
    Add a phone number to the DNC list via the Zoom Admin Portal.
    Raises DNCError on failure. Logs actions and errors for traceability.
    """
    try:
        log_info(f"Navigating to DNC management page: {DNC_MANAGEMENT_URL}")
        driver.get(DNC_MANAGEMENT_URL)
        # Use robust Selenium helpers for reliability
        safe_click(driver, By.ID, "add-dnc-btn")
        wait_and_fill(driver, By.ID, "phone-input", phone_number)
        safe_click(driver, By.ID, "save-btn")
        # Check for success/failure (update this as needed for your UI)
        if "success" not in driver.page_source.lower():
            log_error("DNC add failed: Success message not found in page source.")
            raise DNCError("DNC add failed: Success message not found in page source.")
        log_info(f"Successfully added {phone_number} to DNC list.")  # Success path
        # @see docs/design_doc.md, reference/legacy_code/T1/utils/selenium_utils.py
    except Exception as e:
        log_error(f"Exception during DNC add: {e}")
        raise DNCError(f"Exception during DNC add: {e}")
