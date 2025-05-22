"""Base browser interface and common functionality."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Callable, Type, cast
from functools import wraps
import logging
import time

# Import custom exceptions
from .exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError,
    ElementNotFoundError,
    ElementNotInteractableError,
    TimeoutError,
    ScreenshotError
)

# Type variable for generic typing
T = TypeVar('T')

class BaseBrowser(ABC):
    """Abstract base class defining the browser interface."""
    
    def __init__(self, config: Any, logger: Optional[logging.Logger] = None):
        """Initialize the browser with the given configuration.
        
        Args:
            config: Configuration object for the browser
            logger: Optional logger instance (will create one if not provided)
        """
        self.config = config
        self._driver = None
        self._service = None
        
        # Set up logging
        if logger is None:
            self._logger = logging.getLogger(self.__class__.__name__)
        else:
            self._logger = logger
    
    @abstractmethod
    def start(self) -> None:
        """Start the browser instance."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the browser instance."""
        pass
    
    @abstractmethod
    def navigate_to(self, url: str, wait_time: Optional[float] = None) -> bool:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            wait_time: Optional time to wait for page load
            
        Returns:
            bool: True if navigation was successful
        """
        pass
    
    @abstractmethod
    def get_page_source(self) -> str:
        """Get the current page source.
        
        Returns:
            str: The page source HTML
        """
        pass
    
    @abstractmethod
    def get_current_url(self) -> str:
        """Get the current URL.
        
        Returns:
            str: The current URL
        """
        pass
    
    @abstractmethod
    def take_screenshot(self, file_path: str, full_page: bool = False) -> bool:
        """Take a screenshot of the current page.
        
        Args:
            file_path: Path to save the screenshot
            full_page: If True, capture the full page
            
        Returns:
            bool: True if screenshot was successful
        """
        pass
    
    def is_running(self) -> bool:
        """Check if the browser is running.
        
        Returns:
            bool: True if the browser is running
        """
        return self._driver is not None
    
    @property
    def driver(self) -> Any:
        """Get the WebDriver instance.
        
        Returns:
            The WebDriver instance
            
        Raises:
            BrowserNotInitializedError: If the browser is not running
        """
        if self._driver is None:
            raise BrowserNotInitializedError("Browser is not running")
        return self._driver
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying a function when exceptions occur.
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay between retries
        exceptions: Tuple of exceptions to catch and retry on
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            retries = 0
            current_delay = delay
            last_exception = None
            
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    retries += 1
                    
                    if retries > max_retries:
                        break
                        
                    # Log the retry attempt
                    logger = None
                    if args and hasattr(args[0], '_logger'):
                        logger = args[0]._logger
                    
                    if logger:
                        logger.warning(
                            f"Attempt {retries}/{max_retries} failed: {str(e)}. "
                            f"Retrying in {current_delay:.1f} seconds..."
                        )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # If we get here, all retries failed
            if last_exception:
                if logger:
                    logger.error(f"All {max_retries} attempts failed. Last error: {str(last_exception)}")
                raise last_exception
            else:
                raise RuntimeError("Unexpected error in retry decorator")
        
        return cast(Callable[..., T], wrapper)
    return decorator
