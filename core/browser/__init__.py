"""
Browser automation module for Chrome Puppet.

This module provides a high-level interface for browser automation using Selenium WebDriver.
It includes Chrome-specific implementations, element handling, navigation, and screenshot utilities.

Key Components:
    - ChromeBrowser: Core browser control implementation
    - ChromeConfig: Configuration container for browser settings
    - ElementHelper: Utilities for element interaction
    - NavigationMixin: Common navigation functionality
    - ScreenshotHelper: Screenshot capture utilities

Example:
    >>> from core.browser.chrome import ChromeBrowser
    >>> from core.config import ChromeConfig
    >>> config = ChromeConfig(headless=True)
    >>> with ChromeBrowser(config=config) as browser:
    ...     browser.start()
    ...     browser.navigate_to("https://example.com")
    ...     title = browser.driver.title

Module Structure:
    - browser/
        - __init__.py       # Public API
        - base.py           # Base browser interface
        - chrome.py         # Chrome implementation
        - exceptions.py     # Custom exceptions
        - features/         # Feature modules
            - __init__.py
            - element.py    # Element handling
            - navigation.py # Navigation features
            - screenshot.py # Screenshot utilities
        - drivers/          # Browser drivers
        - types.py          # Type definitions
        - utils/            # Utility functions
    ...     browser.take_screenshot("example.png")
    ...     browser.stop()
"""

# Import key components to make them available at the package level
from .base import BaseBrowser, retry_on_failure
from .drivers.chrome_driver import ChromeDriver
from .element import ElementHelper
from .navigation import NavigationMixin, wait_for_page_load
from .screenshot import ScreenshotHelper
from .exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError,
    ElementNotFoundError,
    ElementNotInteractableError,
    TimeoutError,
    ScreenshotError
)
from ..config import ChromeConfig

# Version of the browser module
__version__ = '0.1.0'

# Define what gets imported with 'from browser import *'
__all__ = [
    # Browser implementation
    'ChromeBrowser',
    'BaseBrowser',
    
    # Core components
    'ElementHelper',
    'NavigationMixin',
    'ScreenshotHelper',
    'wait_for_page_load',
    'retry_on_failure',
    
    # Configuration
    'ChromeConfig',
    
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
