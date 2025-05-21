"""
Browser automation module for Chrome Puppet.

This module provides a high-level interface for browser automation using Selenium WebDriver.
It includes Chrome-specific implementations, element handling, navigation, and screenshot utilities.
"""

# Import key components to make them available at the package level
from .base import BaseBrowser, retry_on_failure
from .chrome import ChromeBrowser
from .puppet import ChromePuppet
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
    # Main interface
    'ChromePuppet',
    
    # Browser implementations
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
