"""
Browser automation module for Chrome Puppet.

This module provides a high-level interface for browser automation using Selenium WebDriver.
It includes Chrome-specific implementations, element handling, navigation, and screenshot utilities.
"""

# Import key components to make them available at the package level
from .base import BaseBrowser, retry_on_failure

# Lazy import to avoid circular dependencies
ChromeBrowser = None
BaseBrowserDriver = None

def _import_chrome_browser():
    global ChromeBrowser
    if ChromeBrowser is None:
        from .drivers.chrome import ChromeBrowser as CB
        ChromeBrowser = CB
    return ChromeBrowser

def _import_base_driver():
    global BaseBrowserDriver
    if BaseBrowserDriver is None:
        from .drivers.base_driver import BaseDriver as BD
        BaseBrowserDriver = BD
    return BaseBrowserDriver

# For backward compatibility
Browser = _import_chrome_browser()

# Import ChromeBrowser as ChromeDriver for backward compatibility
def get_chrome_driver():
    """Get the Chrome browser driver.
    
    This is kept for backward compatibility. Use ChromeBrowser instead.
    """
    return _import_chrome_browser()

# Import exceptions
try:
    from .exceptions import (
        BrowserError,
        BrowserNotInitializedError,
        NavigationError,
        ElementNotFoundError,
        ElementNotInteractableError,
        TimeoutError,
        ScreenshotError
    )
except ImportError:
    # Handle case where exceptions aren't available yet
    pass

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
