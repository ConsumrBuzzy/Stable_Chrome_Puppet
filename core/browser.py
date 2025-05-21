"""
Legacy browser module for Chrome Puppet.

This module is maintained for backward compatibility. New code should use
the new modular structure in the `core.browser` package.

See MIGRATION_GUIDE.md for details on updating your code.
"""
import os
import sys
import time
import logging
from typing import Optional, Any, Dict, Type, cast, Union, List, Tuple, Callable, TypeVar
from pathlib import Path

# Import the new implementation
from .browser.chrome import ChromeBrowser as NewChromeBrowser
from .browser.element import ElementHelper
from .browser.navigation import NavigationMixin
from .browser.screenshot import ScreenshotHelper
from .browser.exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError,
    ElementNotFoundError,
    ElementNotInteractableError,
    TimeoutError as BrowserTimeoutError,
    ScreenshotError
)
from .config import ChromeConfig, DEFAULT_CONFIG

# Type variable for generic typing
T = TypeVar('T')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromePuppet(NewChromeBrowser):
    """Legacy ChromePuppet class for backward compatibility.
    
    This class extends the new ChromeBrowser implementation to maintain
    backward compatibility with existing code.
    
    Note: New code should use ChromeBrowser from core.browser.chrome instead.
    """
    
    def __init__(self, config: Optional[ChromeConfig] = None):
        """Initialize the ChromePuppet with the given configuration.
        
        Args:
            config: ChromeConfig instance with browser settings. If None, uses defaults.
            
        Raises:
            RuntimeError: If Chrome is not installed or cannot be found
        """
        self._config = config or DEFAULT_CONFIG
        super().__init__(self._config)
        
        # Set up element helper
        self.element = ElementHelper(self)
        
        # Set up screenshot helper
        self.screenshot = ScreenshotHelper(self)
        
        # Ensure screenshots directory exists
        screenshots_dir = Path("screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # Legacy method aliases for backward compatibility
    def navigate_to(self, url: str, wait_time: Optional[float] = None) -> bool:
        """Legacy method alias for get()."""
        return self.get(url, wait_time=wait_time)
    
    def quit(self) -> None:
        """Legacy method alias for close()."""
        self.close()
    
    def take_screenshot(self, prefix: str = "screenshot", element: Optional[Any] = None) -> Optional[Path]:
        """Legacy method for taking screenshots.
        
        Args:
            prefix: Prefix for the screenshot filename
            element: Optional WebElement to capture
            
        Returns:
            Path to the saved screenshot or None if failed
        """
        try:
            screenshots_dir = Path("screenshots")
            screenshots_dir.mkdir(exist_ok=True)
            
            # Generate a unique filename
            timestamp = int(time.time())
            file_path = screenshots_dir / f"{prefix}_{timestamp}.png"
            
            # Use the new screenshot helper
            if element is not None:
                self.screenshot.take_element_screenshot(element, str(file_path))
            else:
                self.screenshot.take_screenshot(str(file_path))
                
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def get_soup(self, url: Optional[str] = None) -> Any:
        """Get the page source as a BeautifulSoup object.
        
        Args:
            url: Optional URL to navigate to before getting the page source.
                If None, uses the current page.
                
        Returns:
            BeautifulSoup object or None if an error occurs.
        """
        try:
            from bs4 import BeautifulSoup
            
            if url is not None:
                self.get(url)
                
            return BeautifulSoup(self.driver.page_source, 'html.parser') if self.driver else None
            
        except Exception as e:
            logger.error(f"Failed to get page source: {e}")
            return None
    
    # Legacy property for backward compatibility
    @property
    def driver(self) -> Any:
        """Legacy property to access the WebDriver instance."""
        return getattr(self, '_driver', None)
    
    @driver.setter
    def driver(self, value: Any) -> None:
        """Legacy property setter for WebDriver instance."""
        self._driver = value
    
    # Context manager and cleanup methods
    def __enter__(self) -> 'ChromePuppet':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - ensure resources are cleaned up."""
        self.close()
    
    def __del__(self) -> None:
        """Destructor - ensure resources are cleaned up."""
        try:
            self.close()
        except Exception:
            pass

# Legacy function for backward compatibility
def is_chrome_installed() -> bool:
    """Check if Chrome is installed on the system.
    
    Returns:
        bool: True if Chrome is installed, False otherwise
    """
    try:
        from .browser.chrome import ChromeBrowser
        return ChromeBrowser.is_chrome_installed()
    except Exception as e:
        logger.warning(f"Error checking Chrome installation: {e}")
        return False
