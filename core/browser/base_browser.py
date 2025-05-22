"""Base browser implementation with common functionality."""
import logging
from typing import Any, Optional, Type, TypeVar, Callable
from functools import wraps

from .interfaces import IBrowser
from ..exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError,
    ElementNotFoundError,
    ElementNotInteractableError,
    TimeoutError,
    ScreenshotError
)

T = TypeVar('T', bound='BaseBrowser')

def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,)
):
    """Decorator for retrying a function when exceptions occur.
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay between retries
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self: 'BaseBrowser', *args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(self, *args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                        
                    self._logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception if last_exception else Exception("Unknown error in retry decorator")
        
        return wrapper
    return decorator

class BaseBrowser(IBrowser):
    """Base browser implementation with common functionality."""
    
    def __init__(self, config: Any, logger: Optional[logging.Logger] = None):
        """Initialize the browser with the given configuration.
        
        Args:
            config: Configuration object for the browser
            logger: Optional logger instance
        """
        self.config = config
        self._driver = None
        self._service = None
        self._is_running = False
        self._logger = logger or logging.getLogger(self.__class__.__name__)
    
    @property
    def is_running(self) -> bool:
        """Check if the browser is running."""
        return self._is_running
    
    def _ensure_running(self) -> None:
        """Ensure the browser is running."""
        if not self.is_running:
            raise BrowserNotInitializedError("Browser is not running")
    
    def _ensure_driver(self) -> None:
        """Ensure the WebDriver is initialized."""
        if self._driver is None:
            raise BrowserNotInitializedError("WebDriver is not initialized")
    
    @retry_on_failure()
    def navigate_to(self, url: str, wait_time: Optional[float] = None) -> bool:
        """Navigate to the specified URL."""
        self._ensure_running()
        self._ensure_driver()
        
        try:
            self._logger.info(f"Navigating to: {url}")
            self._driver.get(url)
            
            if wait_time is not None:
                time.sleep(wait_time)
                
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to navigate to {url}: {e}")
            raise NavigationError(f"Failed to navigate to {url}") from e
    
    def get_page_source(self) -> str:
        """Get the current page source."""
        self._ensure_running()
        self._ensure_driver()
        return self._driver.page_source
    
    def get_current_url(self) -> str:
        """Get the current URL."""
        self._ensure_running()
        self._ensure_driver()
        return self._driver.current_url
    
    def take_screenshot(self, file_path: str, full_page: bool = False) -> bool:
        """Take a screenshot of the current page."""
        self._ensure_running()
        self._ensure_driver()
        
        try:
            if full_page:
                self._take_full_page_screenshot(file_path)
            else:
                self._driver.save_screenshot(file_path)
            return True
        except Exception as e:
            self._logger.error(f"Failed to take screenshot: {e}")
            raise ScreenshotError("Failed to take screenshot") from e
    
    def _take_full_page_screenshot(self, file_path: str) -> None:
        """Take a screenshot of the full page (to be implemented by subclasses)."""
        raise NotImplementedError("Full page screenshot not implemented")
