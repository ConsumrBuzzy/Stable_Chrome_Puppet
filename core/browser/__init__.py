"""
Browser automation module for Chrome Puppet.

This module provides a high-level interface for browser automation using Selenium WebDriver.
It includes Chrome-specific implementations, element handling, navigation, and screenshot utilities.
"""

# Import key components to make them available at the package level
from .base import BaseBrowser, retry_on_failure
from .features.element import ElementHelper
from .features.navigation import NavigationMixin, wait_for_page_load
from .features.screenshot import ScreenshotHelper
from .exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError,
    ElementNotFoundError,
    ElementNotInteractableError,
    TimeoutError,
    ScreenshotError
)

# Import ChromeDriver using a lazy import pattern to avoid circular imports
ChromeDriver = None
def get_chrome_driver():
    """Lazy import for ChromeDriver to avoid circular imports."""
    global ChromeDriver
    if ChromeDriver is None:
        from .drivers.chrome_driver import ChromeDriver as CD
        ChromeDriver = CD
    return ChromeDriver

# Version of the browser module
__version__ = '0.2.0'

# Define what gets imported with 'from browser import *'
__all__ = [
    # Browser implementation
    'BaseBrowser',
    'ChromeDriver',
    'get_chrome_driver',
    
    # Core components
    'ElementHelper',
    'NavigationMixin',
    'ScreenshotHelper',
    'wait_for_page_load',
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
