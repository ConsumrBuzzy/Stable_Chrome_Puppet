"""Browser module providing a generic interface for browser automation.

This module provides a high-level interface for browser automation with support
for multiple browser backends through a driver-based architecture.
"""
import logging
import time
from typing import Any, Optional, Type, Union, Dict, List, Tuple

from .drivers import get_driver_class, BaseBrowserDriver
from .base import BaseBrowser
from .exceptions import (
    BrowserError, 
    BrowserNotInitializedError,
    NavigationError,
    ScreenshotError
)


class Browser(BaseBrowser):
    """Main browser class providing a generic interface for browser automation.
    
    This class serves as a thin wrapper around browser driver implementations,
    providing a consistent API regardless of the underlying browser.
    """
    
    def __init__(self, config: Any = None, logger: Optional[logging.Logger] = None):
        """Initialize the browser.
        
        Args:
            config: Configuration object containing browser settings.
                   If None, default configuration will be used.
            logger: Optional logger instance for logging.
        """
        if config is None:
            from .config import BrowserConfig
            config = BrowserConfig()
            
        # Initialize the base class with driver=None initially
        super().__init__(config, logger)
        self._driver = None
        self._driver_class: Optional[Type[BaseBrowserDriver]] = None
        self._initialize_driver()
        
        # Set the driver on the base class after initialization
        super().__setattr__('driver', self._driver)
    
    def _initialize_driver(self) -> None:
        """Initialize the browser driver based on configuration."""
        browser_type = getattr(self.config, 'browser_type', 'chrome').lower()
        try:
            self._driver_class = get_driver_class(browser_type)
            self._driver = self._driver_class(self.config, self.logger)
        except ValueError as e:
            self.logger.warning(f"Falling back to Chrome: {e}")
            # Fall back to Chrome if the configured browser is not available
            self._driver_class = get_driver_class('chrome')
            self._driver = self._driver_class(self.config, self.logger)
    
    @property
    def driver(self) -> Any:
        """Get the underlying driver instance."""
        if self._driver is None:
            self.start()
        return self._driver.driver if hasattr(self._driver, 'driver') else self._driver
        
    @driver.setter
    def driver(self, value: Any) -> None:
        """Set the underlying driver instance.
        
        This is primarily for internal use. Prefer using the start() method.
        """
        self._driver = value
    
    def start(self) -> None:
        """Start the browser."""
        if self._driver is None:
            self._initialize_driver()
        self._driver.start()
        
    def navigate_to(self, url: str, wait_time: Optional[float] = None) -> bool:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            wait_time: Optional time to wait for page load
            
        Returns:
            bool: True if navigation was successful
        """
        if self._driver is None:
            self.start()
        return self._driver.navigate_to(url, wait_time)
        
    def get_page_source(self) -> str:
        """Get the current page source.
        
        Returns:
            str: The page source HTML
        """
        if self._driver is None:
            raise BrowserNotInitializedError("Browser is not initialized. Call start() first.")
        return self._driver.get_page_source()
        
    def get_current_url(self) -> str:
        """Get the current URL.
        
        Returns:
            str: The current URL
        """
        if self._driver is None:
            raise BrowserNotInitializedError("Browser is not initialized. Call start() first.")
        return self._driver.get_current_url()
        
    def take_screenshot(self, file_path: str, full_page: bool = False) -> bool:
        """Take a screenshot of the current page.
        
        Args:
            file_path: Path to save the screenshot
            full_page: If True, capture the full page (not supported in all browsers)
            
        Returns:
            bool: True if screenshot was successful
        """
        if self._driver is None:
            raise BrowserNotInitializedError("Browser is not initialized. Call start() first.")
        return self._driver.take_screenshot(file_path, full_page)
        
    def is_running(self) -> bool:
        """Check if the browser is running.
        
        Returns:
            bool: True if the browser is running
        """
        if self._driver is None:
            return False
        return self._driver.is_running()
    
    def stop(self) -> None:
        """Stop the browser and clean up resources."""
        if self._driver is not None:
            try:
                self._driver.stop()
            except Exception as e:
                self.logger.error(f"Error stopping browser: {e}")
            finally:
                self._driver = None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def __getattr__(self, name):
        """Delegate attribute access to the underlying driver."""
        # Don't try to delegate special methods
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
            
        # If we have a driver, try to get the attribute from it
        if self._driver is not None:
            return getattr(self._driver, name)
            
        # If we get here, the attribute wasn't found
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


# For backward compatibility
ChromeBrowser = Browser
