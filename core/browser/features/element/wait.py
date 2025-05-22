"""Element wait functionality."""
from typing import Callable, Optional, Any, Type, TypeVar, Union
from functools import wraps
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException
)

from ..exceptions import TimeoutError as BrowserTimeoutError

T = TypeVar('T', bound=Callable)

def retry_on_stale_element(max_retries: int = 3, delay: float = 0.5) -> Callable[[T], T]:
    """Decorator to retry a function when a stale element reference occurs.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: T) -> T:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except StaleElementReferenceException as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        continue
                    raise BrowserTimeoutError("Element is no longer attached to the DOM") from last_exception
            return None
        return wrapper  # type: ignore
    return decorator

class ElementWaitMixin:
    """Mixin class providing element wait functionality."""
    
    def wait_for_element(
        self,
        by: str,
        value: str,
        timeout: float = 10,
        poll_frequency: float = 0.5,
        ignored_exceptions: Optional[list] = None
    ) -> Any:
        """Wait for an element to be present in the DOM.
        
        Args:
            by: The locator strategy (e.g., 'id', 'xpath', 'css_selector')
            value: The locator value
            timeout: Maximum time to wait in seconds
            poll_frequency: How often to check for the element
            ignored_exceptions: List of exception classes to ignore
            
        Returns:
            The WebElement once it is found
            
        Raises:
            BrowserTimeoutError: If the element is not found within the timeout
        """
        if ignored_exceptions is None:
            ignored_exceptions = [NoSuchElementException]
            
        try:
            return WebDriverWait(
                self.driver,
                timeout,
                poll_frequency=poll_frequency,
                ignored_exceptions=ignored_exceptions
            ).until(EC.presence_of_element_located((by, value)))
        except TimeoutException as e:
            raise BrowserTimeoutError(f"Timed out waiting for element {by}={value}") from e
    
    def wait_for_element_visible(
        self,
        by: str,
        value: str,
        timeout: float = 10,
        poll_frequency: float = 0.5
    ) -> Any:
        """Wait for an element to be visible in the DOM.
        
        Args:
            by: The locator strategy (e.g., 'id', 'xpath', 'css_selector')
            value: The locator value
            timeout: Maximum time to wait in seconds
            poll_frequency: How often to check for the element
            
        Returns:
            The WebElement once it is visible
            
        Raises:
            BrowserTimeoutError: If the element is not visible within the timeout
        """
        try:
            return WebDriverWait(
                self.driver,
                timeout,
                poll_frequency=poll_frequency
            ).until(EC.visibility_of_element_located((by, value)))
        except TimeoutException as e:
            raise BrowserTimeoutError(f"Timed out waiting for element {by}={value} to be visible") from e
    
    def wait_for_element_clickable(
        self,
        by: str,
        value: str,
        timeout: float = 10,
        poll_frequency: float = 0.5
    ) -> Any:
        """Wait for an element to be clickable.
        
        Args:
            by: The locator strategy (e.g., 'id', 'xpath', 'css_selector')
            value: The locator value
            timeout: Maximum time to wait in seconds
            poll_frequency: How often to check for the element
            
        Returns:
            The WebElement once it is clickable
            
        Raises:
            BrowserTimeoutError: If the element is not clickable within the timeout
        """
        try:
            return WebDriverWait(
                self.driver,
                timeout,
                poll_frequency=poll_frequency
            ).until(EC.element_to_be_clickable((by, value)))
        except TimeoutException as e:
            raise BrowserTimeoutError(f"Timed out waiting for element {by}={value} to be clickable") from e
