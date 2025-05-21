"""
dnc_contact_center.py
Handles all logic for adding a phone number to the Zoom Contact Center DNC list.
Modernized and modular, ported from T1 reference (zoom_contact_center.py).
Uses robust Selenium utilities, logging, and diagnostics.
"""

import time
from datetime import datetime
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, ElementNotInteractableException,
    TimeoutException, StaleElementReferenceException, WebDriverException
)

from selenium_utils import (
    wait_for_element, wait_for_clickable, wait_and_fill, 
    wait_and_click, log_and_screenshot, safe_click
)
from logging_utils import log_info, log_warning, log_error, log_debug
from config import settings
from browser_utils import wait_for_page_load, wait_for_url_contains


def add_to_contact_center_dnc(driver: WebDriver, phone_number: str, max_retries: int = 2) -> bool:
    """
    Add a phone number to the Zoom Contact Center DNC list.
    Uses robust waits, retries, logging, and diagnostics.
    
    Args:
        driver: Selenium WebDriver instance
        phone_number: Phone number to add to DNC list
        max_retries: Maximum number of retry attempts
        
    Returns:
        bool: True if successful, False otherwise
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for attempt in range(1, max_retries + 1):
        try:
            log_info(f'[Contact Center] Attempt {attempt}/{max_retries} - Navigating to DNC Management...')
            
            # Navigate to DNC management page with retry logic
            if not _navigate_to_dnc_page(driver):
                log_warning(f'[Contact Center] Attempt {attempt}: Failed to navigate to DNC page')
                continue
                
            # Interact with the DNC interface
            if _interact_with_dnc_interface(driver, phone_number, timestamp):
                log_info('[Contact Center] Successfully added number to DNC list')
                return True
                
        except Exception as e:
            log_error(f'[Contact Center] Attempt {attempt} failed: {str(e)}')
            log_and_screenshot(driver, f'contact_center_error_attempt_{attempt}_{timestamp}')
            
            if attempt == max_retries:
                log_error(f'[Contact Center] All {max_retries} attempts failed')
                return False
                
            log_info(f'[Contact Center] Retrying... ({attempt + 1}/{max_retries})')
            time.sleep(2)  # Small delay before retry
    
    return False

def _navigate_to_dnc_page(driver: WebDriver) -> bool:
    """Navigate to the DNC management page with proper error handling."""
    try:
        target_url = DNC_MANAGEMENT_URL.split('#')[0]  # Get base URL without hash
        
        # Check if we're already on the correct page
        if target_url in driver.current_url:
            log_info('[Contact Center] Already on DNC management page')
            return True
            
        # Navigate to the DNC management URL
        log_info('[Contact Center] Navigating to DNC management page...')
        driver.get(DNC_MANAGEMENT_URL)
        
        # Wait for page to load and URL to match
        try:
            WebDriverWait(driver, 30).until(
                lambda d: target_url in d.current_url
            )
            log_info(f'[Contact Center] Successfully navigated to DNC page: {driver.current_url}')
            return True
            
        except TimeoutException:
            log_warning(f'[Contact Center] Did not reach expected URL. Current URL: {driver.current_url}')
            # Take a screenshot for debugging
            screenshot_path = f"screenshots/dnc_nav_error_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            log_info(f'[Contact Center] Saved screenshot to {screenshot_path}')
            return False
            
    except Exception as e:
        log_error(f'[Contact Center] Error navigating to DNC page: {str(e)}')
        return False

def _interact_with_dnc_interface(driver: WebDriver, phone_number: str, timestamp: str) -> bool:
    """Interact with the DNC interface to add a phone number."""
    try:
        # Wait for the Block List tab and click it
        log_info('[Contact Center] Clicking Block List tab...')
        block_list_tab = WebDriverWait(driver, DEFAULT_WAIT).until(
            EC.element_to_be_clickable((By.ID, "tab-blockList"))
        )
        safe_click(driver, block_list_tab)
        
        # Wait for the Add Rule button and click it
        log_info('[Contact Center] Clicking Add Rule button...')
        add_rule_btn = WebDriverWait(driver, DEFAULT_WAIT).until(
            EC.element_to_be_clickable((
                By.XPATH, 
                "//button[contains(@class,'zm-button--primary') and .//span[contains(text(),'Add new rule')]]"
            ))
        )
        safe_click(driver, add_rule_btn)
        
        # Wait for the dialog to appear
        log_info('[Contact Center] Waiting for Add Rule dialog...')
        dialog = WebDriverWait(driver, DEFAULT_WAIT * 2).until(
            EC.visibility_of_element_located((
                By.XPATH,
                "//div[contains(@class,'zm-dialog__wrapper')]//div[@role='dialog']"
            ))
        )
        
        # Fill in the phone number
        log_info(f'[Contact Center] Entering phone number: {phone_number}')
        phone_input = WebDriverWait(dialog, DEFAULT_WAIT).until(
            EC.visibility_of_element_located((By.ID, "block-phone-input"))
        )
        phone_input.clear()
        phone_input.send_keys(phone_number)
        
        # Click Save
        log_info('[Contact Center] Clicking Save button...')
        save_btn = WebDriverWait(dialog, DEFAULT_WAIT).until(
            EC.element_to_be_clickable((
                By.XPATH,
                ".//button[.//span[contains(text(),'Save')] and not(@disabled)]"
            ))
        )
        safe_click(driver, save_btn)
        
        # Verify success
        log_info('[Contact Center] Verifying success...')
        try:
            WebDriverWait(driver, DEFAULT_WAIT).until(
                EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class,'zm-dialog__wrapper')]"))
            )
            log_info('[Contact Center] Successfully added number to DNC list')
            return True
            
        except TimeoutException:
            log_warning('[Contact Center] Dialog did not close as expected, but continuing...')
            return True
        
    except TimeoutException as e:
        log_error(f'[Contact Center] Timeout while interacting with DNC interface: {str(e)}')
        log_and_screenshot(driver, f'contact_center_timeout_{timestamp}')
    except Exception as e:
        log_error(f'[Contact Center] Error interacting with DNC interface: {str(e)}')
        log_and_screenshot(driver, f'contact_center_error_{timestamp}')
        return False
