"""
Browser automation module for Chrome Puppet.

This module provides a high-level interface for browser automation using Selenium WebDriver.
It includes Chrome-specific implementations, element handling, navigation, and screenshot utilities.
"""

# Import key components to make them available at the package level
from .base import BaseBrowser, retry_on_failure
from .drivers.chrome import ChromeBrowser
from .drivers.base_driver import BaseBrowserDriver
from .exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError,
    ElementNotFoundError,
    ElementNotInteractableError,
    TimeoutError,
    ScreenshotError
)

# For backward compatibility
Browser = ChromeBrowser

# Import ChromeBrowser as ChromeDriver for backward compatibility
def get_chrome_driver():
    """Get the Chrome browser driver.
    
    This is kept for backward compatibility. Use ChromeBrowser instead.
    """
    from .drivers.chrome import ChromeBrowser
    return ChromeBrowser

# Version of the browser module
__version__ = '0.2.0'

# Define what gets imported with 'from browser import *'
__all__ = [
    # Browser implementations
    'BaseBrowser',
    'ChromeBrowser',
    'Browser',  # Alias for ChromeBrowser for backward compatibility
    'BaseBrowserDriver',
    
    # Core components
    'retry_on_failure',
    
    # Exceptions
    'BrowserError',
    'BrowserNotInitializedError',
    'NavigationError',
    'ElementNotFoundError',
    'ElementNotInteractableError',
    'TimeoutError',
    'ScreenshotError',
    
    # Version
    '__version__'
]
