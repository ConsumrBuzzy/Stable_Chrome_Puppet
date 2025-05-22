"""Browser module providing a generic interface for browser automation.

This module provides a high-level interface for browser automation with support
for multiple browser backends through a driver-based architecture.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional, Type, Union, Dict, List, Tuple, cast, TypeVar, Generic, Type

from .drivers import get_driver_class, BaseBrowserDriver
from .base import BaseBrowser
from .exceptions import (
    BrowserError, 
    BrowserNotInitializedError,
    NavigationError,
    ScreenshotError
)

T = TypeVar('T', bound=BaseBrowserDriver)


class Browser(BaseBrowser):
    """Main browser class providing a generic interface for browser automation.
    
    This class serves as a thin wrapper around browser driver implementations,
    providing a consistent API regardless of the underlying browser.
    """
    
    def __init__(self, config: Any = None, logger: Optional[logging.Logger] = None) -> None:
        """Initialize the browser.
        
        Args:
            config: Configuration object containing browser settings.
                   If None, default configuration will be used.
            logger: Optional logger instance for logging.
        """
        if config is None:
            from .config import BrowserConfig
            config = BrowserConfig()
        
        # Set up logging before initializing base class
        if logger is None:
            logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize the base class with driver=None
        super().__init__(config, logger)
        
        # Initialize driver-related attributes
        self._driver: Optional[BaseBrowserDriver] = None
        self._driver_class: Optional[Type[BaseBrowserDriver]] = None
        self._initialized: bool = False
        self._config = config
        self._logger = logger
    
    def _initialize_driver(self) -> None:
        """Initialize the browser driver based on configuration.
        
        Raises:
            BrowserError: If driver initialization fails
        """
        if self._initialized and self._driver is not None:
            return
            
        browser_type = getattr(self._config, 'browser_type', 'chrome').lower()
        try:
            self._driver_class = get_driver_class(browser_type)
            self._driver = self._driver_class(self._config, self._logger)
            self._driver.start()
            
            # Set the driver instance on the base class
            if hasattr(self._driver, 'driver'):
                # If the driver has a 'driver' attribute, use that
                super().__setattr__('_driver_instance', self._driver.driver)
            else:
                # Otherwise use the driver itself
                super().__setattr__('_driver_instance', self._driver)
                
        except Exception as e:
            self._logger.error(f"Failed to initialize {browser_type} driver: {e}")
            if browser_type != 'chrome':
                self._logger.warning("Falling back to Chrome driver")
                try:
                    self._driver_class = get_driver_class('chrome')
                    self._driver = self._driver_class(self._config, self._logger)
                    self._driver.start()
                    
                    # Set the driver instance on the base class
                    if hasattr(self._driver, 'driver'):
                        super().__setattr__('_driver_instance', self._driver.driver)
                    else:
                        super().__setattr__('_driver_instance', self._driver)
                        
                except Exception as chrome_error:
                    self._logger.error(f"Failed to initialize Chrome driver: {chrome_error}")
                    self._driver = None
                    raise BrowserError("Failed to initialize any browser driver") from chrome_error
            else:
                self._driver = None
                raise BrowserError(f"Failed to initialize {browser_type} driver") from e
            
        self._initialized = True
    
    @property
    def driver(self) -> Any:
        """Get the underlying driver instance.
        
        Returns:
            The underlying WebDriver instance
            
        Raises:
            BrowserNotInitializedError: If the browser is not initialized
        """
        if not hasattr(self, '_driver_instance') or self._driver_instance is None:
            raise BrowserNotInitializedError("Browser is not initialized. Call start() first.")
        return self._driver_instance
        
    @driver.setter
    def driver(self, value: Any) -> None:
        """Set the underlying driver instance.
        
        Args:
            value: The WebDriver instance to use
            
        Note:
            This is primarily for internal use. Prefer using the start() method.
        """
        if value is not None:
            driver_instance = value.driver if hasattr(value, 'driver') else value
            super().__setattr__('_driver_instance', driver_instance)
        else:
            super().__setattr__('_driver_instance', None)
    
    def start(self) -> None:
        """Start the browser.
        
        Raises:
            BrowserError: If the browser fails to start
        """
        if self._initialized and self._driver is not None:
            self._logger.warning("Browser is already started")
            return
            
        try:
            self._initialize_driver()
            if self._driver is None:
                raise BrowserError("Failed to initialize browser driver")
                
            self._logger.info(f"Started {self._driver.__class__.__name__}")
            
        except Exception as e:
            self._logger.error(f"Failed to start browser: {e}", exc_info=True)
            self.stop()
            raise BrowserError(f"Failed to start browser: {e}") from e
        
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
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying driver.
        
        Args:
            name: Name of the attribute to get
            
        Returns:
            The requested attribute from the underlying driver
            
        Raises:
            AttributeError: If the attribute doesn't exist on the driver
            BrowserNotInitializedError: If the browser is not initialized
        """
        # Don't try to delegate special methods
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
            
        # Check if the attribute exists on this class
        if name in self.__dict__ or name in self.__class__.__dict__:
            return object.__getattribute__(self, name)
            
        # If we have a driver, try to get the attribute from it
        if self._driver is None:
            raise BrowserNotInitializedError("Browser is not initialized. Call start() first.")
            
        try:
            return getattr(self._driver, name)
        except AttributeError as e:
            # Re-raise with a more helpful message
            raise AttributeError(
                f"'{self.__class__.__name__}' object and its driver have no attribute '{name}'"
            ) from e
                
    # Removed the extra raise statement here


# For backward compatibility
ChromeBrowser = Browser
