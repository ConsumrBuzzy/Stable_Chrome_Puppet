"""
dnc_alt.py
Handles the logic for adding a phone number to the alternate DNC system within the Zoom Admin Portal.
Stub for future expansion; selectors and logic should be updated as needed.
"""
from config import DNC_ALT_URL, DEFAULT_WAIT  # DNC_ALT_URL should be defined in config
from selenium.webdriver.common.by import By
from utils.logging_utils import log_info, log_error
from utils.exceptions import DNCError
from utils.selenium_utils import wait_for_element, safe_click, wait_and_fill


def add_to_dnc_alt(driver, phone_number):
    """
    Add a phone number to the alternate DNC list via the Zoom Admin Portal.
    Raises DNCError on failure. Logs actions and errors for traceability.
    """
    try:
        log_info(f"Navigating to Alternate DNC management page: {DNC_ALT_URL}")
        driver.get(DNC_ALT_URL)
        safe_click(driver, By.ID, "add-alt-dnc-btn")  # Update selectors as needed
        wait_and_fill(driver, By.ID, "alt-phone-input", phone_number)
        safe_click(driver, By.ID, "alt-save-btn")
        # Check for success/failure (update this as needed for your UI)
        if "success" not in driver.page_source.lower():
            log_error("Alt DNC add failed: Success message not found in page source.")
            raise DNCError("Alt DNC add failed: Success message not found in page source.")
        log_info(f"Successfully added {phone_number} to alternate DNC list.")
    except Exception as e:
        log_error(f"Exception during alternate DNC add: {e}")
        raise DNCError(f"Exception during alternate DNC add: {e}")
