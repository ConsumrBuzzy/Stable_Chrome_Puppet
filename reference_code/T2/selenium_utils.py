"""
selenium_utils.py - Enhanced Selenium utilities with viewport awareness

Provides robust element interaction with viewport management, smooth scrolling,
and human-like behavior simulation for reliable browser automation.
"""
import time
import random
import logging
from typing import Any, Optional, Tuple, Callable, TypeVar, Type, Union, Dict
from functools import wraps

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    WebDriverException
)

from browser_utils import ViewportState, ScrollDirection

# Configure logging
logger = logging.getLogger(__name__)

# Type aliases
Locator = Union[WebElement, Tuple[str, str]]
T = TypeVar('T', bound=Any)

def retry_on_stale(
    max_retries: int = 3,
    delay: float = 0.5
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry a function when StaleElementReferenceException occurs.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Base delay between retries in seconds (will be randomized)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except StaleElementReferenceException as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    # Randomize delay to avoid patterns
                    time.sleep(delay * (attempt + 1) * random.uniform(0.8, 1.2))
            raise last_exception or RuntimeError("Unexpected error in retry_on_stale")
        return wrapper
    return decorator

def ensure_element_visible(
    driver: WebDriver,
    element: WebElement,
    viewport: Optional[ViewportState] = None,
    scroll_margin: int = 50,
    timeout: float = 10.0
) -> bool:
    """
    Ensure an element is visible in the viewport.
    
    Args:
        driver: WebDriver instance
        element: The element to make visible
        viewport: Optional ViewportState instance
        scroll_margin: Margin in pixels when scrolling
        timeout: Maximum time to wait for element to be visible
        
    Returns:
        bool: True if element is visible, False otherwise
    """
    try:
        viewport = viewport or ViewportState(driver)
        if not viewport.is_element_in_viewport(element, margin=scroll_margin):
            viewport.ensure_element_visible(element, scroll_margin=scroll_margin)
        return True
    except Exception as e:
        logger.warning(f"Failed to make element visible: {e}")
        return False

def wait_for_element(
    driver: WebDriver,
    locator: Locator,
    timeout: float = 20.0,
    poll_frequency: float = 0.5,
    ignore_errors: bool = False
) -> Optional[WebElement]:
    """
    Wait for an element to be present in the DOM and return it.
    
    Args:
        driver: WebDriver instance
        locator: Either a WebElement or a tuple of (By, value)
        timeout: Maximum time to wait in seconds
        poll_frequency: How often to check for the element
        ignore_errors: If True, returns None instead of raising an exception
        
    Returns:
        WebElement if found, None otherwise
    """
    try:
        if isinstance(locator, WebElement):
            return locator
            
        by, value = locator
        wait = WebDriverWait(
            driver,
            timeout=timeout,
            poll_frequency=poll_frequency,
            ignored_exceptions=(StaleElementReferenceException,)
        )
        return wait.until(EC.presence_of_element_located((by, value)))
    except TimeoutException:
        if ignore_errors:
            return None
        raise

@retry_on_stale(max_retries=3)
def safe_click(
    driver: WebDriver,
    locator: Locator,
    viewport: Optional[ViewportState] = None,
    timeout: float = 20.0,
    scroll_into_view: bool = True,
    scroll_margin: int = 50,
    max_attempts: int = 2
) -> WebElement:
    """
    Safely click an element with retries and viewport handling.
    
    Args:
        driver: WebDriver instance
        locator: Either a WebElement or a tuple of (By, value)
        viewport: Optional ViewportState instance
        timeout: Maximum time to wait for element to be clickable
        scroll_into_view: Whether to scroll the element into view
        scroll_margin: Margin in pixels when scrolling
        max_attempts: Maximum number of click attempts
        
    Returns:
        The clicked WebElement
        
    Raises:
        ElementNotInteractableException: If element cannot be clicked after all attempts
    """
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            # Get the element with retry on stale
            element = wait_for_element(driver, locator, timeout) if not isinstance(locator, WebElement) else locator
            
            # Ensure element is visible if requested
            if scroll_into_view:
                ensure_element_visible(driver, element, viewport, scroll_margin, timeout)
            
            # Wait for element to be clickable with a shorter timeout per attempt
            wait = WebDriverWait(driver, timeout / max_attempts)
            element = wait.until(EC.element_to_be_clickable(element))
            
            # Add human-like delay before clicking
            time.sleep(random.uniform(0.1, 0.3))
            
            # Try to click using JavaScript as a fallback
            try:
                element.click()
            except WebDriverException as click_error:
                logger.warning(f"Standard click failed, trying JavaScript click (attempt {attempt}/{max_attempts}): {click_error}")
                driver.execute_script("arguments[0].click();", element)
            
            # Add small delay after clicking
            time.sleep(random.uniform(0.1, 0.2))
            
            return element
            
        except (TimeoutException, WebDriverException) as e:
            last_exception = e
            logger.warning(f"Click attempt {attempt} failed: {str(e)}")
            
            # Take a screenshot for debugging
            if attempt < max_attempts:
                log_and_screenshot(
                    driver,
                    f"Click attempt {attempt} failed, retrying...",
                    f"click_retry_{attempt}"
                )
                time.sleep(0.5)  # Small delay before retry
    
    # If we get here, all attempts failed
    error_msg = f"Failed to click element after {max_attempts} attempts: {str(last_exception)}"
    log_and_screenshot(driver, error_msg, "click_failed")
    raise ElementNotInteractableException(error_msg) from last_exception

def safe_send_keys(
    driver: WebDriver,
    locator: Locator,
    text: str,
    clear_first: bool = True,
    viewport: Optional[ViewportState] = None,
    timeout: float = 10.0,
    scroll_into_view: bool = True
) -> WebElement:
    """
    Safely send keys to an element with retries and viewport handling.
    
    Args:
        driver: WebDriver instance
        locator: Either a WebElement or a tuple of (By, value)
        text: Text to send to the element
        clear_first: Whether to clear the element first
        viewport: Optional ViewportState instance
        timeout: Maximum time to wait for element to be interactable
        scroll_into_view: Whether to scroll the element into view
        
    Returns:
        The WebElement that received the keys
    """
    # Get the element with retry on stale
    element = wait_for_element(driver, locator, timeout) if not isinstance(locator, WebElement) else locator
    
    # Ensure element is visible if requested
    if scroll_into_view:
        ensure_element_visible(driver, element, viewport)
    
    # Wait for element to be interactable
    wait = WebDriverWait(driver, timeout)
    element = wait.until(EC.element_to_be_clickable(element))
    
    # Clear the field if requested
    if clear_first:
        element.clear()
        time.sleep(0.1)  # Small delay after clear
    
    # Type with human-like delays
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))  # Human-like typing speed
    
    return element


def log_and_screenshot(
    driver: WebDriver,
    message: str,
    tag: str = "diagnostic",
    include_viewport_info: bool = True,
    include_page_source: bool = False
) -> str:
    """
    Log a message and save a screenshot with additional diagnostic information.
    
    Args:
        driver: WebDriver instance
        message: Message to log
        tag: Tag for the screenshot filename
        include_viewport_info: Whether to include viewport information
        include_page_source: Whether to save page source
        
    Returns:
        str: Path to the saved screenshot, or empty string if failed
    """
    import os
    from datetime import datetime
    from .logging_utils import log_error, log_warning
    
    try:
        # Create shots directory if it doesn't exist
        shots_dir = os.path.join(os.getcwd(), 'shots')
        os.makedirs(shots_dir, exist_ok=True)
        
        # Generate timestamp and filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = os.path.join(shots_dir, f'{tag}_{timestamp}.png')
        
        # Take screenshot
        driver.save_screenshot(screenshot_path)
        
        # Log the message with screenshot path
        log_msg = f"[Diagnostics] {message} (Screenshot: {screenshot_path})"
        
        # Add viewport information if requested
        if include_viewport_info:
            try:
                viewport = ViewportState(driver)
                width, height = viewport.size
                log_msg += f"\nViewport: {width}x{height}"
            except Exception as e:
                log_warning(f"Failed to get viewport info: {e}")
        
        # Save page source if requested
        if include_page_source:
            try:
                source_path = os.path.join(shots_dir, f'{tag}_{timestamp}.html')
                with open(source_path, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                log_msg += f"\nPage source: {source_path}"
            except Exception as e:
                log_warning(f"Failed to save page source: {e}")
        
        log_error(log_msg)
        return screenshot_path
        
    except Exception as e:
        log_error(f"[Diagnostics] Failed to save diagnostic information: {e}. Original message: {message}")
        return ""

def wait_for_page_load(
    driver: WebDriver,
    timeout: float = 30.0,
    check_ready_state: bool = True,
    check_jquery: bool = False
) -> bool:
    """
    Wait for the page to finish loading.
    
    Args:
        driver: WebDriver instance
        timeout: Maximum time to wait in seconds
        check_ready_state: Whether to check document.readyState
        check_jquery: Whether to check for jQuery.active
        
    Returns:
        bool: True if page loaded successfully, False otherwise
    """
    try:
        wait = WebDriverWait(driver, timeout)
        
        # Check document.readyState
        if check_ready_state:
            wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        
        # Check jQuery.active if needed
        if check_jquery:
            wait.until(lambda d: d.execute_script('return (typeof jQuery === "undefined") || (jQuery.active === 0)'))
        
        return True
        
    except TimeoutException:
        log_warning(f"Page did not finish loading within {timeout} seconds")
        return False

def scroll_into_view(
    driver: WebDriver,
    element: WebElement,
    block: str = 'center',
    behavior: str = 'smooth',
    margin: int = 50,
    viewport: Optional[ViewportState] = None
) -> None:
    """
    Scroll an element into view with smooth animation.
    
    Args:
        driver: WebDriver instance
        element: Element to scroll to
        block: Vertical alignment ('start', 'center', 'end', 'nearest')
        behavior: Scroll behavior ('auto' or 'smooth')
        margin: Margin in pixels
        viewport: Optional ViewportState instance
    """
    try:
        viewport = viewport or ViewportState(driver)
        viewport.ensure_element_visible(element, scroll_margin=margin)
    except Exception as e:
        log_warning(f"Failed to scroll element into view: {e}")
        # Fallback to direct scroll
        driver.execute_script("arguments[0].scrollIntoView();", element)
