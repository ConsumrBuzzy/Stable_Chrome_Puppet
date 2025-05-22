"""Page load waiting functionality."""
from typing import Callable, Optional, Any, Type, TypeVar, Union
from functools import wraps
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from ..exceptions import TimeoutError as BrowserTimeoutError

T = TypeVar('T', bound=Callable)

class NavigationWaitMixin:
    """Mixin class providing page load waiting functionality."""
    
    def wait_for_page_load(self, timeout: float = 30, poll_frequency: float = 0.5) -> None:
        """Wait for the page to finish loading.
        
        Args:
            timeout: Maximum time to wait in seconds
            poll_frequency: How often to check for page load
            
        Raises:
            BrowserTimeoutError: If the page doesn't load within the timeout
        """
        try:
            WebDriverWait(
                self.driver,
                timeout,
                poll_frequency=poll_frequency
            ).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException as e:
            raise BrowserTimeoutError("Timed out waiting for page to load") from e
    
    def wait_for_url_contains(
        self,
        text: str,
        timeout: float = 10,
        poll_frequency: float = 0.5
    ) -> bool:
        """Wait until the URL contains the given text.
        
        Args:
            text: The text to wait for in the URL
            timeout: Maximum time to wait in seconds
            poll_frequency: How often to check the URL
            
        Returns:
            True if the URL contains the text, False otherwise
            
        Raises:
            BrowserTimeoutError: If the URL doesn't contain the text within the timeout
        """
        try:
            return WebDriverWait(
                self.driver,
                timeout,
                poll_frequency=poll_frequency
            ).until(EC.url_contains(text))
        except TimeoutException as e:
            raise BrowserTimeoutError(f"Timed out waiting for URL to contain: {text}") from e
    
    def wait_for_url_matches(
        self,
        pattern: str,
        timeout: float = 10,
        poll_frequency: float = 0.5
    ) -> bool:
        """Wait until the URL matches the given regex pattern.
        
        Args:
            pattern: The regex pattern to match against the URL
            timeout: Maximum time to wait in seconds
            poll_frequency: How often to check the URL
            
        Returns:
            True if the URL matches the pattern, False otherwise
            
        Raises:
            BrowserTimeoutError: If the URL doesn't match the pattern within the timeout
        """
        import re
        
        def url_matches(driver: Any) -> bool:
            current_url = driver.current_url
            return bool(re.search(pattern, current_url))
            
        try:
            return WebDriverWait(
                self.driver,
                timeout,
                poll_frequency=poll_frequency
            ).until(url_matches)
        except TimeoutException as e:
            raise BrowserTimeoutError(f"Timed out waiting for URL to match pattern: {pattern}") from e
