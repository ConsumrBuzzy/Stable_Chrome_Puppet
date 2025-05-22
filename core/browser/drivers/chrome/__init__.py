"""Chrome browser driver implementation.

This package provides the Chrome browser driver implementation for the browser automation
framework. It uses Selenium WebDriver under the hood to control a Chrome browser instance.
"""
from typing import Optional, Type, TypeVar

from core.browser.config import ChromeConfig
from core.browser.drivers.base import BaseDriver
from .browser import ChromeBrowser

# Re-export the ChromeBrowser class
__all__ = ['ChromeBrowser', 'create_driver']

# Type variable for type hints
T = TypeVar('T', bound='ChromeBrowser')

def create_driver(config: Optional[ChromeConfig] = None) -> ChromeBrowser:
    """Create a new Chrome browser instance.
    
    Args:
        config: Optional configuration for the browser.
        
    Returns:
        A new ChromeBrowser instance.
    """
    return ChromeBrowser(config=config)
