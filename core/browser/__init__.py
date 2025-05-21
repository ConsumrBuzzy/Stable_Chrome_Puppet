"""
Browser automation module for Chrome Puppet.

This module provides a high-level interface for browser automation using Selenium WebDriver.
It includes Chrome-specific implementations, element handling, navigation, and screenshot utilities.
"""

# Import key components to make them available at the package level
from .base import BaseBrowser, retry_on_failure
from .chrome import ChromeBrowser
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

# Version of the browser module
__version__ = '0.1.0'

# Define what gets imported with 'from browser import *'
__all__ = [
    'BaseBrowser',
    'ChromeBrowser',
    'ElementHelper',
    'NavigationMixin',
    'ScreenshotHelper',
    'retry_on_failure',
    'wait_for_page_load',
    'BrowserError',
    'BrowserNotInitializedError',
    'NavigationError',
    'ElementNotFoundError',
    'ElementNotInteractableError',
    'TimeoutError',
    'ScreenshotError',
    '__version__'
]
