"""Base driver interface for browser automation.

This module defines the abstract base class that all browser drivers must implement.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, Generic, Type

from core.browser.base import BaseBrowser
from core.browser.config import BrowserConfig

# Type variable for generic typing
T = TypeVar('T', bound='BaseDriver')

class BaseDriver(ABC):
    """Abstract base class for browser drivers.
    
    This class defines the interface that all browser drivers must implement.
    """
    
    def __init__(self, config: BrowserConfig):
        """Initialize the browser driver with the given configuration.
        
        Args:
            config: Configuration for the browser driver.
        """
        self.config = config
    
    @abstractmethod
    def create_browser(self) -> BaseBrowser:
        """Create and return a new browser instance.
        
        Returns:
            A new browser instance.
            
        Raises:
            BrowserError: If the browser cannot be created.
        """
        pass
    
    @classmethod
    def create(cls: Type[T], config: Optional[BrowserConfig] = None) -> BaseBrowser:
        """Create a new browser instance using this driver.
        
        This is a convenience method that creates a new driver instance
        and uses it to create a browser.
        
        Args:
            config: Optional configuration for the browser. If not provided,
                   a default configuration will be used.
                   
        Returns:
            A new browser instance.
            
        Raises:
            BrowserError: If the browser cannot be created.
        """
        if config is None:
            config = BrowserConfig()
        return cls(config).create_browser()
