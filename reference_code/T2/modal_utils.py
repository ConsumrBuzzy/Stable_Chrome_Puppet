"""
modal_utils.py

Utilities for robustly finding and interacting with modal dialogs/popups in Selenium workflows.
Includes hybrid Selenium + BS4 diagnostics for debugging element-finding issues in dynamic modals.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from typing import Optional, List
import logging

# Initialize logger
logger = logging.getLogger(__name__)


def find_dialog_by_title(driver, title: str, timeout: int = 10) -> Optional[object]:
    """
    Finds a visible dialog/modal by its title text.
    Returns the dialog WebElement or None if not found.
    Logs and screenshots all visible dialogs if not found.
    """
    try:
        wait = WebDriverWait(driver, timeout)
        dialog = wait.until(EC.visibility_of_element_located((
            By.XPATH,
            f"//div[contains(@class,'zm-dialog__wrapper')]//div[@role='dialog' and .//span[contains(@class,'zm-dialog__title') and normalize-space(text())='{title}']]"
        )))
        return dialog
    except TimeoutException:
        logger.warning(f"Dialog with title '{title}' not found after {timeout}s.")
        log_visible_dialogs_bs4(driver.page_source)
        return None


def log_visible_dialogs_bs4(html: str) -> None:
    """
    Uses BS4 to log all visible dialog/modal titles and their structure for diagnostics.
    """
    soup = BeautifulSoup(html, "html.parser")
    dialogs = soup.select("div.zm-dialog__wrapper div[role='dialog']")
    for i, dialog in enumerate(dialogs, 1):
        title_elem = dialog.select_one("span.zm-dialog__title")
        title = title_elem.get_text(strip=True) if title_elem else "(no title)"
        logger.info(f"Dialog {i}: title='{title}'")
        logger.debug(f"Dialog {i} HTML: {str(dialog)[:400]}...")


def find_element_in_dialog(dialog, by, value, timeout: int = 5) -> Optional[object]:
    """
    Finds an element inside a dialog WebElement, waiting up to timeout seconds.
    Returns the element or None.
    """
    try:
        wait = WebDriverWait(dialog, timeout)
        return wait.until(lambda d: d.find_element(by, value))
    except Exception as e:
        logger.error(f"Error finding element {by}={value} in dialog: {e}")
        return None


def robust_click_in_dialog(dialog, by, value, timeout: int = 5) -> bool:
    """
    Waits for and clicks an element inside a dialog. Returns True if successful.
    """
    el = find_element_in_dialog(dialog, by, value, timeout)
    if el:
        try:
            el.click()
            return True
        except Exception as e:
            logging.error(f"[modal_utils] Failed to click element in dialog: {e}")
    return False
