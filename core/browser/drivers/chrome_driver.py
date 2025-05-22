"""Chrome browser driver implementation."""
import logging
import os
import platform
import shutil
import struct
import sys
import zipfile
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Type, TypeVar, Callable

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager, ChromeType

from ..base import BaseBrowser
from ..driver_config import DriverConfig
from ..exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError,
    ScreenshotError,
    ElementNotFoundError,
    ElementNotInteractableError,
    TimeoutError as BrowserTimeoutError
)
from ..features.element import ElementHelper
from ..features.navigation import NavigationMixin
from ..features.screenshot import ScreenshotHelper
from . import register_driver, BaseBrowserDriver

# Type variable for generic typing
T = TypeVar('T')

# Type alias for WebDriver
WebDriver = ChromeWebDriver


@register_driver("chrome")
class ChromeDriver(BaseBrowserDriver, NavigationMixin, ElementHelper, ScreenshotHelper):
    """Chrome browser driver implementation.
    
    This class provides a high-level interface for browser automation with Chrome,
    including navigation, element interaction, and screenshot capabilities.
    """
    
    def __init__(self, config: Any, logger: Optional[logging.Logger] = None):
        """Initialize the Chrome browser.
        
        Args:
            config: Configuration object containing browser settings
            logger: Optional logger instance for logging
        """
        super().__init__(config, logger)
        self.driver: Optional[WebDriver] = None
        self._service: Optional[ChromeService] = None
        self._options: Optional[ChromeOptions] = None
        self._setup_options()
    
    @classmethod
    def get_name(cls) -> str:
        """Get the name of the browser driver.
        
        Returns:
            str: The name of the browser ("chrome")
        """
        return "chrome"
    
    def _setup_options(self) -> None:
        """Set up Chrome options based on configuration."""
        self._options = ChromeOptions()
        
        # Add Chrome arguments from config
        chrome_args = getattr(self.config, 'chrome_args', [])
        for arg in chrome_args:
            if arg not in self._options.arguments:
                self._options.add_argument(arg)
        
        # Add experimental options if provided
        experimental_options = getattr(self.config, 'experimental_options', {})
        for key, value in experimental_options.items():
            self._options.add_experimental_option(key, value)
        
        # Set window size if specified
        if hasattr(self.config, 'window_size') and self.config.window_size:
            width, height = self.config.window_size
            self._options.add_argument(f'--window-size={width},{height}')
    
    def _create_service(self) -> ChromeService:
        """Create and configure the Chrome service.
        
        Returns:
            ChromeService: Configured Chrome service instance
        """
        driver_config = getattr(self.config, 'driver_config', DriverConfig())
        
        # Set up service arguments
        service_args = driver_config.service_args or []
        
        # Create service with configured options
        service = ChromeService(
            executable_path=driver_config.driver_path or ChromeDriverManager().install(),
            service_args=service_args,
            log_path=driver_config.service_log_path
        )
        
        return service
    
    def start(self) -> None:
        """Start the Chrome browser."""
        if self.driver is not None:
            self.logger.warning("Browser is already running")
            return
        
        try:
            # Set up Chrome service and options
            self._service = self._create_service()
            
            # Initialize Chrome WebDriver
            self.driver = webdriver.Chrome(
                service=self._service,
                options=self._options
            )
            
            # Configure timeouts
            if hasattr(self.config, 'implicit_wait'):
                self.driver.implicitly_wait(self.config.implicit_wait)
                
            if hasattr(self.config, 'page_load_timeout'):
                self.driver.set_page_load_timeout(self.config.page_load_timeout)
                
            if hasattr(self.config, 'script_timeout'):
                self.driver.set_script_timeout(self.config.script_timeout)
                
            self.logger.info("Chrome browser started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Chrome browser: {e}")
            self._cleanup_resources()
            raise BrowserError(f"Failed to start Chrome browser: {e}") from e
            
    def _cleanup_resources(self) -> None:
        """Clean up any resources used by the browser."""
        try:
            if self._service:
                self._service.stop()
                self._service = None
        except Exception as e:
            self.logger.warning(f"Error cleaning up Chrome service: {e}")
    
    def stop(self) -> None:
        """Stop the Chrome browser and clean up resources."""
        if self.driver is None:
            return
            
        try:
            self.logger.info("Stopping Chrome browser...")
            self.driver.quit()
            self.logger.info("Chrome browser stopped")
        except Exception as e:
            self.logger.error(f"Error stopping Chrome browser: {e}")
            raise
        finally:
            self.driver = None
            self._cleanup_resources()
    
    def is_running(self) -> bool:
        """Check if the browser is running.
        
        Returns:
            bool: True if the browser is running, False otherwise
        """
        try:
            return self.driver is not None and self.driver.service.is_connectable()
        except Exception:
            return False
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def __getattr__(self, name):
        """Delegate attribute access to the underlying driver."""
        if self.driver is None:
            raise BrowserNotInitializedError(
                "Browser driver not initialized. Call start() first."
            )
        return getattr(self.driver, name)
    
    @property
    def current_url(self) -> str:
        """Get the current URL."""
        if self.driver is None:
            raise BrowserNotInitializedError("Browser is not running")
        return self.driver.current_url
    
    @property
    def title(self) -> str:
        """Get the current page title."""
        if self.driver is None:
            raise BrowserNotInitializedError("Browser is not running")
        return self.driver.title
    
    def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript in the current browser context."""
        if self.driver is None:
            raise BrowserNotInitializedError("Browser is not running")
        return self.driver.execute_script(script, *args)
    
    def get(self, url: str) -> None:
        """Navigate to the specified URL."""
        if self.driver is None:
            raise BrowserNotInitializedError("Browser is not running")
        try:
            self.driver.get(url)
            self.logger.debug(f"Navigated to: {url}")
        except TimeoutException as e:
            error_msg = f"Timeout while navigating to {url}"
            self.logger.error(error_msg)
            raise BrowserTimeoutError(error_msg) from e
        except WebDriverException as e:
            error_msg = f"Failed to navigate to {url}: {str(e)}"
            self.logger.error(error_msg)
            raise NavigationError(error_msg) from e
