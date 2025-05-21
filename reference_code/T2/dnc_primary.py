"""
dnc_primary.py
Handles the logic for adding a phone number to the primary DNC system within the Zoom Admin Portal.
Modular, robust, and inspired by T1 reference.
"""
from config import DNC_MANAGEMENT_URL, DEFAULT_WAIT
from selenium.webdriver.common.by import By
from utils.logging_utils import log_info, log_error
from utils.exceptions import DNCError
from utils.selenium_utils import wait_for_element, safe_click, wait_and_fill


def add_to_dnc_primary(driver, phone_number):
    """
    Add a phone number to the primary DNC list via the Zoom Admin Portal.
    Raises DNCError on failure. Logs actions and errors for traceability.
    """
    try:
        log_info(f"Navigating to DNC management page: {DNC_MANAGEMENT_URL}")
        driver.get(DNC_MANAGEMENT_URL)
        safe_click(driver, By.ID, "add-dnc-btn")
        wait_and_fill(driver, By.ID, "phone-input", phone_number)
        safe_click(driver, By.ID, "save-btn")
        # Check for success/failure (update this as needed for your UI)
        if "success" not in driver.page_source.lower():
            log_error("DNC add failed: Success message not found in page source.")
            raise DNCError("DNC add failed: Success message not found in page source.")
        log_info(f"Successfully added {phone_number} to DNC list.")
    except Exception as e:
        log_error(f"Exception during DNC add: {e}")
        raise DNCError(f"Exception during DNC add: {e}")
