"""Page navigation and waiting functionality."""
from typing import Optional, Callable, Any, TypeVar, Union, Tuple
from functools import wraps
import time

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException
)

from .exceptions import (
    NavigationError,
    TimeoutError as BrowserTimeoutError
)

T = TypeVar('T')

def wait_for_page_load(timeout: float = 30.0) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to wait for page load after a navigation action.
    
    Args:
        timeout: Maximum time to wait for page load
        
    Returns:
        Decorated function with page load waiting
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(self, *args, **kwargs) -> T:
            if not hasattr(self, 'driver') or not hasattr(self.driver, 'execute_script'):
                return func(self, *args, **kwargs)
                
            # Execute the navigation function
            result = func(self, *args, **kwargs)
            
            # Wait for page to be in ready state
            try:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            except TimeoutException as e:
                raise BrowserTimeoutError(
                    f"Page did not finish loading within {timeout} seconds"
                ) from e
                
            return result
        return wrapper
    return decorator

class NavigationMixin:
    """Mixin class providing navigation functionality."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the navigation mixin."""
        super().__init__(*args, **kwargs)
        self._last_url = None
    
    @wait_for_page_load()
    def navigate_to(self, url: str, wait_time: Optional[float] = None) -> bool:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            wait_time: Optional time to wait for page load after navigation
            
        Returns:
            bool: True if navigation was successful
            
        Raises:
            NavigationError: If navigation fails
        """
        if not hasattr(self, 'driver'):
            raise NavigationError("Browser is not initialized")
            
        try:
            self._last_url = self.driver.current_url if hasattr(self.driver, 'current_url') else None
            self.driver.get(url)
            
            # Additional wait if specified
            if wait_time and wait_time > 0:
                time.sleep(wait_time)
                
            return True
            
        except WebDriverException as e:
            raise NavigationError(f"Failed to navigate to {url}: {str(e)}") from e
    
    def refresh(self) -> None:
        """Refresh the current page."""
        if not hasattr(self, 'driver'):
            raise NavigationError("Browser is not initialized")
            
        try:
            self.driver.refresh()
        except WebDriverException as e:
            raise NavigationError(f"Failed to refresh page: {str(e)}") from e
    
    def back(self) -> None:
        """Navigate back in browser history."""
        if not hasattr(self, 'driver'):
            raise NavigationError("Browser is not initialized")
            
        try:
            self.driver.back()
        except WebDriverException as e:
            raise NavigationError(f"Failed to navigate back: {str(e)}") from e
    
    def forward(self) -> None:
        """Navigate forward in browser history."""
        if not hasattr(self, 'driver'):
            raise NavigationError("Browser is not initialized")
            
        try:
            self.driver.forward()
        except WebDriverException as e:
            raise NavigationError(f"Failed to navigate forward: {str(e)}") from e
    
    def wait_for_url_change(
        self,
        url: Optional[str] = None,
        timeout: float = 10.0
    ) -> bool:
        """Wait for the URL to change from the current or specified URL.
        
        Args:
            url: The URL to wait to change from (defaults to current URL)
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if URL changed within timeout, False otherwise
        """
        if not hasattr(self, 'driver'):
            return False
            
        current_url = url or (self.driver.current_url if hasattr(self.driver, 'current_url') else None)
        if not current_url:
            return False
            
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.current_url != current_url
            )
            return True
        except TimeoutException:
            return False
    
    def wait_for_url_contains(
        self,
        text: str,
        timeout: float = 10.0
    ) -> bool:
        """Wait for the URL to contain the specified text.
        
        Args:
            text: Text to wait for in the URL
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if URL contains text within timeout, False otherwise
        """
        if not hasattr(self, 'driver') or not text:
            return False
            
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: text in d.current_url
            )
            return True
        except TimeoutException:
            return False
    
    def wait_for_page_title_contains(
        self,
        text: str,
        timeout: float = 10.0
    ) -> bool:
        """Wait for the page title to contain the specified text.
        
        Args:
            text: Text to wait for in the page title
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if page title contains text within timeout, False otherwise
        """
        if not hasattr(self, 'driver') or not text:
            return False
            
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: text.lower() in d.title.lower()
            )
            return True
        except TimeoutException:
            return False
    
    def wait_for_condition(
        self,
        condition: Callable[[WebDriver], bool],
        timeout: float = 10.0,
        message: str = ""
    ) -> bool:
        """Wait for a custom condition to be true.
        
        Args:
            condition: Callable that takes a WebDriver and returns a boolean
            timeout: Maximum time to wait in seconds
            message: Optional message for timeout exception
            
        Returns:
            bool: True if condition becomes true within timeout
            
        Raises:
            BrowserTimeoutError: If condition is not met within timeout
        """
        if not hasattr(self, 'driver') or not callable(condition):
            return False
            
        try:
            WebDriverWait(self.driver, timeout).until(condition)
            return True
        except TimeoutException as e:
            if message:
                raise BrowserTimeoutError(message) from e
            raise BrowserTimeoutError(
                f"Condition not met within {timeout} seconds"
            ) from e
