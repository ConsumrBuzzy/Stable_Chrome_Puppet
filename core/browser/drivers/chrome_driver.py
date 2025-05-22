"""Chrome browser driver implementation."""
import os
import sys
import platform
import shutil
import struct
import zipfile
import urllib.request
import logging
from pathlib import Path
from typing import Optional, Any, Dict, Tuple, Union

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from ..base import BaseBrowser
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
        self.driver = None
        self._service = None
        self._options = None
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
        
        # Set headless mode if configured
        if getattr(self.config, 'headless', False):
            self._options.add_argument('--headless=new')
        
        # Set window size if specified
        if hasattr(self.config, 'window_size'):
            width, height = self.config.window_size
            self._options.add_argument(f'--window-size={width},{height}')
        
        # Add additional Chrome arguments if provided
        if hasattr(self.config, 'chrome_args'):
            for arg in self.config.chrome_args:
                self._options.add_argument(arg)
        
        # Set experimental options if provided
        if hasattr(self.config, 'chrome_experimental_options'):
            for key, value in self.config.chrome_experimental_options.items():
                self._options.add_experimental_option(key, value)
    
    def start(self) -> None:
        """Start the Chrome browser."""
        if self.driver is not None:
            self.logger.warning("Browser is already running")
            return
        
        try:
            # Set up Chrome service
            chrome_service = Service(ChromeDriverManager().install())
            
            # Initialize Chrome WebDriver
            self.driver = webdriver.Chrome(service=chrome_service, options=self._options)
            
            # Set implicit wait if specified
            if hasattr(self.config, 'implicit_wait'):
                self.driver.implicitly_wait(self.config.implicit_wait)
            
            # Set page load timeout if specified
            if hasattr(self.config, 'page_load_timeout'):
                self.driver.set_page_load_timeout(self.config.page_load_timeout)
            
            # Set script timeout if specified
            if hasattr(self.config, 'script_timeout'):
                self.driver.set_script_timeout(self.config.script_timeout)
            
            self.logger.info("Chrome browser started successfully")
            
        except Exception as e:
            error_msg = f"Failed to start Chrome browser: {str(e)}"
            self.logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def stop(self) -> None:
        """Stop the Chrome browser."""
        if self.driver is None:
            self.logger.warning("No active browser session to stop")
            return
        
        try:
            self.driver.quit()
            self.driver = None
            self._service = None
            self.logger.info("Browser stopped successfully")
        except Exception as e:
            error_msg = f"Error while stopping browser: {str(e)}"
            self.logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
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
