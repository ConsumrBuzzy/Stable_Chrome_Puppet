llow"""Browser module providing a generic interface for browser automation.

This module provides a high-level interface for browser automation with support
for multiple browser backends, defaulting to Chrome.
"""
import logging
from typing import Any, Optional

from .drivers import get_driver_class
from .base import BaseBrowser


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
            
        super().__init__(config, logger)
        self._driver = None
        self._initialize_driver()
    
    def _initialize_driver(self) -> None:
        """Initialize the browser driver based on configuration."""
        browser_type = getattr(self.config, 'browser_type', 'chrome').lower()
        try:
            driver_class = get_driver_class(browser_type)
            self._driver = driver_class(self.config, self.logger)
        except ValueError as e:
            self.logger.warning(f"Falling back to Chrome: {e}")
            # Fall back to Chrome if the configured browser is not available
            driver_class = get_driver_class('chrome')
            self._driver = driver_class(self.config, self.logger)
    
    def start(self) -> None:
        """Start the browser."""
        if self._driver is None:
            self._initialize_driver()
        self._driver.start()
    
    def stop(self) -> None:
        """Stop the browser."""
        if self._driver is not None:
            self._driver.stop()
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def __getattr__(self, name):
        """Delegate attribute access to the underlying driver."""
        if self._driver is None:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return getattr(self._driver, name)


# For backward compatibility
ChromeBrowser = Browser
