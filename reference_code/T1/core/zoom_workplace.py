"""
zoom_workplace.py
Handles all logic for adding a phone number to the Zoom Workplace DNC list.
Uses robust, modular utilities for web automation.
"""
import time
import logging
from typing import Any
from utils.logging_utils import log_info, log_warning, log_error
from utils.screenshot_utils import save_screenshot
from config import ZOOM_WORKPLACE_URL, DEFAULT_WAIT
from utils.selenium_utils import wait_for_element, wait_for_clickable, wait_and_fill, wait_and_click, log_and_screenshot
from selenium.webdriver.common.by import By


def add_to_workplace_dnc(driver: Any, phone_number: str) -> None:
    """
    Navigate and add phone number to Zoom Workplace DNC.
    Uses robust waits, retries, and logging. Modular and maintainable.
    """
    try:
        # 1. Go to Workplace Telephone page
        log_info('[Workplace] Navigating to Workplace Telephone page...' )
        driver.get(ZOOM_WORKPLACE_URL)
        # Wait for Block List tab to be clickable (page loaded)
        log_info('[Workplace] Waiting for Block List Tab (id="tab-blockList") to be clickable...')
        wait_and_click(driver, By.ID, "tab-blockList", timeout=DEFAULT_WAIT)
        log_info('[Workplace] Block List Tab found and clicked.')

        wait_and_click(driver, By.ID, "add-rule-btn", timeout=DEFAULT_WAIT)
        log_info('[Workplace] Add Rule Button found and clicked.')

        log_info('[Workplace] Waiting for Block List Table (id="block-list-table")...')
        try:
            block_table = wait_for_element(driver, By.ID, "block-list-table", timeout=DEFAULT_WAIT)
            log_info('[Workplace] Block List Table found.')
        except Exception as e:
            log_and_screenshot(driver, f'[Workplace] Timeout: Block List Table not found. Exception: {type(e).__name__}, URL: {driver.current_url}', 'workplace_block_list_table_error')
            return

        log_info(f'[Workplace] Entering phone number: {phone_number}...')
        try:
            wait_and_fill(driver, By.ID, "block-phone-input", phone_number, timeout=DEFAULT_WAIT)
            log_info('[Workplace] Phone number entered.')
        except Exception as e:
            log_and_screenshot(driver, f'[Workplace] Failed to enter phone number. Exception: {type(e).__name__}, URL: {driver.current_url}', 'workplace_phone_input_error')
            return

        # 6. Select Block Type
        log_info('[Workplace] Selecting Block Type: Inbound, Outbound...')
        try:
            wait_and_click(driver, By.ID, "block-type-dropdown", timeout=DEFAULT_WAIT)
            for call_type in ['Inbound', 'Outbound']:
                wait_and_click(driver, By.XPATH, f"//span[contains(text(),'{call_type}')]")
                log_info(f'[Workplace] Block Type selected: {call_type}')
            wait_and_click(driver, By.ID, "block-type-dropdown", timeout=DEFAULT_WAIT)  # Close dropdown
        except Exception as e:
            log_and_screenshot(driver, f'[Workplace] Failed to select block type. Exception: {type(e).__name__}, URL: {driver.current_url}', 'workplace_block_type_error')
            return

        # 7. Click Save
        log_info('[Workplace] Clicking Save button...')
        try:
            wait_and_click(driver, By.ID, "save-block-btn", timeout=DEFAULT_WAIT)
            log_info('[Workplace] Save button clicked.')
        except Exception as e:
            log_and_screenshot(driver, f'[Workplace] Failed to click Save button. Exception: {type(e).__name__}, URL: {driver.current_url}', 'workplace_save_btn_error')
            return

        # 8. Wait for Success Toast
        log_info('[Workplace] Waiting for success toast...')
        try:
            toast = wait_for_element(driver, By.CLASS_NAME, "zm-toast-success", timeout=DEFAULT_WAIT)
            msg = toast.text
            log_info(f'[Workplace] Success: {msg}')
        except Exception as e:
            log_and_screenshot(driver, f'[Workplace] No confirmation detected after Save. Exception: {type(e).__name__}, URL: {driver.current_url}', 'workplace_save_error')
            return
    except Exception as e:
        log_error(f"Workplace DNC failed: {e}")
        raise
