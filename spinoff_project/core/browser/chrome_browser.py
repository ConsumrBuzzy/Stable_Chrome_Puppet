"""Chrome browser implementation using Selenium WebDriver.

This module provides a high-level interface for Chrome browser automation,
including page navigation, element interaction, and browser management.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Type, TypeVar

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    JavascriptException
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.shadowroot import ShadowRoot
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from core.browser import BaseBrowser, BrowserError, NavigationError
from core.config import ChromeConfig

# Type variables
T = TypeVar('T', bound='ChromeBrowser')
ElementType = Union[WebElement, ShadowRoot]

class ChromeBrowser(BaseBrowser):
    """Chrome browser implementation with enhanced functionality.
    
    This class provides a high-level interface for Chrome browser automation,
    including page navigation, element interaction, and browser management.
    """
    
    def __init__(self, config: Optional[ChromeConfig] = None, logger: Optional[logging.Logger] = None):
        """Initialize the Chrome browser with the given configuration.
        
        Args:
            config: Chrome browser configuration. If None, default settings will be used.
            logger: Optional logger instance. If None, a default logger will be created.
        """
        from core.config import ChromeConfig
        super().__init__(config or ChromeConfig(), logger)
        self._service: Optional[ChromeService] = None
    
    def start(self) -> None:
        """Start the Chrome browser with the configured settings."""
        if self._driver is not None:
            self._logger.warning("Browser is already running")
            return
            
        try:
            options = self._create_chrome_options()
            self._service = ChromeService()
            
            try:
                # First try with the default ChromeDriver
                self._driver = webdriver.Chrome(service=self._service, options=options)
            except WebDriverException as e:
                self._logger.warning("Falling back to webdriver-manager: %s", e)
                # Fall back to webdriver-manager if ChromeDriver not found
                self._service = ChromeService(ChromeDriverManager().install())
                self._driver = webdriver.Chrome(service=self._service, options=options)
            
            # Configure timeouts
            self._driver.set_page_load_timeout(self.config.page_load_timeout)
            self._driver.set_script_timeout(self.config.script_timeout)
            
            if self.config.implicit_wait > 0:
                self._driver.implicitly_wait(self.config.implicit_wait)
                
            self._logger.info("Chrome browser started successfully")
            
        except Exception as e:
            self._logger.error("Failed to start Chrome browser: %s", e, exc_info=True)
            self.close()
            raise BrowserError(f"Failed to start Chrome browser: {e}") from e
    
    def _create_chrome_options(self) -> ChromeOptions:
        """Create ChromeOptions based on the configuration."""
        options = ChromeOptions()
        
        # Basic options
        if self.config.headless:
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
        
        # Window size
        width, height = self.config.window_size
        options.add_argument(f'--window-size={width},{height}')
        
        # Performance options
        if self.config.disable_gpu:
            options.add_argument('--disable-gpu')
        
        if self.config.no_sandbox:
            options.add_argument('--no-sandbox')
            
        if self.config.disable_dev_shm_usage:
            options.add_argument('--disable-dev-shm-usage')
            
        if self.config.disable_extensions:
            options.add_argument('--disable-extensions')
            
        if self.config.disable_infobars:
            options.add_argument('--disable-infobars')
        
        # User data directory
        if self.config.user_data_dir:
            options.add_argument(f'--user-data-dir={self.config.user_data_dir}')
        
        # Proxy settings
        if self.config.proxy_server:
            options.add_argument(f'--proxy-server={self.config.proxy_server}')
        
        # User agent
        if self.config.user_agent:
            options.add_argument(f'--user-agent={self.config.user_agent}')
        
        # Security options
        options.set_capability('acceptInsecureCerts', self.config.accept_insecure_certs)
        
        if self.config.ignore_certificate_errors:
            options.add_argument('--ignore-certificate-errors')
        
        # Experimental options
        for name, value in (self.config.experimental_options or {}).items():
            options.set_capability(f'goog:{name}', value)
        
        # Preferences
        if self.config.prefs:
            options.add_experimental_option('prefs', self.config.prefs)
        
        # Extensions
        for ext in (self.config.extensions or []):
            if isinstance(ext, (str, Path)) and os.path.isfile(ext):
                options.add_extension(ext)
        
        # Additional arguments
        for arg in (self.config.arguments or []):
            options.add_argument(arg)
            
        return options
    
    def wait_for_element(
        self,
        by: str,
        value: str,
        timeout: float = 10.0,
        poll_frequency: float = 0.5
    ) -> WebElement:
        """Wait for an element to be present in the DOM and visible.
        
        Args:
            by: The search strategy (e.g., 'id', 'xpath', 'css_selector')
            value: The value to search for
            timeout: Maximum time to wait in seconds
            poll_frequency: How often to check for the element
            
        Returns:
            The found WebElement
            
        Raises:
            TimeoutException: If the element is not found within the timeout
        """
        return WebDriverWait(
            self.driver,
            timeout=timeout,
            poll_frequency=poll_frequency
        ).until(EC.presence_of_element_located((by, value)))
    
    def take_screenshot(self, file_path: str, full_page: bool = False) -> bool:
        """Take a screenshot of the current page.
        
        Args:
            file_path: Path to save the screenshot
            full_page: Whether to capture the full page (requires page to be scrollable)
            
        Returns:
            bool: True if screenshot was taken successfully, False otherwise
        """
        try:
            if full_page:
                return self._take_full_page_screenshot(file_path)
                
            self.driver.save_screenshot(file_path)
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to take screenshot: {e}")
            return False
    
    def _take_full_page_screenshot(self, file_path: str) -> bool:
        """Take a screenshot of the full page by scrolling and stitching."""
        try:
            # Store original size
            original_size = self.driver.get_window_size()
            
            # Get page dimensions
            total_width = self.driver.execute_script("return document.body.scrollWidth")
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Set viewport size
            self.driver.set_window_size(total_width, total_height)
            
            # Take screenshot
            self.driver.save_screenshot(file_path)
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to take full page screenshot: {e}")
            return False
            
        finally:
            # Restore original size
            if 'original_size' in locals():
                self.driver.set_window_size(
                    original_size['width'],
                    original_size['height']
                )
