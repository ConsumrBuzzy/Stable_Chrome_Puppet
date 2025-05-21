"""
selenium_utils.py - Common Selenium helpers for Zoom DNC Genie
(Replaces element_finder.py)
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Any

def wait_for_element(driver: Any, by: str, value: str, timeout: int = 20):
    """Wait for an element to be present and return it."""
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))

def wait_for_clickable(driver: Any, by: str, value: str, timeout: int = 20):
    """Wait for an element to be clickable and return it."""
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))

def safe_click(driver: Any, by: str, value: str, timeout: int = 20):
    """Wait for an element to be clickable and click it."""
    elem = wait_for_clickable(driver, by, value, timeout)
    elem.click()
    return elem

def wait_for_element_or_url(driver: Any, by: str, value: str, expected_urls, timeout: int = 20, poll_frequency: float = 1.0):
    """
    Wait for either an element to appear or for the URL to change to any of expected_urls.
    Returns 'element' if element found, 'url' if URL matched.
    expected_urls: list or str (will be converted to list)
    """
    import time
    from selenium.common.exceptions import TimeoutException
    if isinstance(expected_urls, str):
        expected_urls = [expected_urls]
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            elem = driver.find_element(by, value)
            if elem.is_displayed():
                return 'element'
        except Exception:
            pass
        current_url = driver.current_url
        if any(url in current_url for url in expected_urls):
            return 'url'
        time.sleep(poll_frequency)
    raise TimeoutException(f"Neither element ({value}) nor expected URL ({expected_urls}) appeared within {timeout} seconds.")


def wait_and_fill(driver: Any, by: str, value: str, text: str, timeout: int = 20):
    """
    Wait for an element, clear it, and send keys. Returns the element.
    """
    elem = wait_for_element(driver, by, value, timeout)
    elem.clear()
    elem.send_keys(text)
    return elem

def wait_and_click(driver: Any, by: str, value: str, timeout: int = 20):
    """
    Wait for an element to be clickable and click it. Returns the element.
    """
    elem = wait_for_clickable(driver, by, value, timeout)
    elem.click()
    return elem

# Centralized error logging and screenshot utility
def log_and_screenshot(driver, message: str, prefix: str):
    from utils.logging_utils import log_error
    from utils.screenshot_utils import save_screenshot
    log_error(message)
    save_screenshot(driver, prefix)
