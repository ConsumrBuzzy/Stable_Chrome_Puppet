"""
Chrome browser implementation for Chrome Puppet.

This module provides a robust implementation of the BaseBrowser interface
for Chrome, with support for both headed and headless modes, automatic
driver management, and comprehensive error handling.
"""
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Tuple, Callable, TypeVar

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException
)

# Local imports
from utils.driver_manager import ChromeDriverManager as LocalChromeDriverManager

# Local imports
from .base import BaseBrowser, retry_on_failure
from .exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError,
    ElementNotFoundError,
    ScreenshotError
)
from ..config import ChromeConfig

# Type variable for generic web elements
WebElementT = TypeVar('WebElementT', bound=WebElement)

class ChromeBrowser(BaseBrowser):
    """
    Chrome browser implementation using Selenium WebDriver.
    
    This class provides a high-level interface for interacting with Chrome,
    including navigation, element interaction, and browser management.
    """
    
    def __init__(self, config: ChromeConfig, logger=None):
        """Initialize the Chrome browser with the given configuration.
        
        Args:
            config: Chrome configuration object containing browser settings
            logger: Optional logger instance for logging browser operations
            
        Raises:
            BrowserError: If there's an issue initializing the browser
        """
        super().__init__(config, logger)
        self.config = config
        self.driver: Optional[WebDriver] = None
        self._service = None
        self._is_running = False
    
    def _get_chrome_driver_path(self) -> str:
        """
        Get the path to the ChromeDriver executable.
        
        Returns:
            str: Path to the ChromeDriver executable
            
        Raises:
            BrowserError: If ChromeDriver cannot be found or installed
        """
        try:
            # Use our local ChromeDriverManager to handle driver installation
            driver_manager = LocalChromeDriverManager(logger=self._logger)
            driver_path = driver_manager.setup_chromedriver()
            self._logger.info(f"Using ChromeDriver from: {driver_path}")
            return str(driver_path)
        except Exception as e:
            error_msg = f"Failed to set up ChromeDriver: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
        
    @retry_on_failure(max_retries=3, delay=2, backoff=2, exceptions=(WebDriverException,))
    def start(self) -> None:
        """
        Start the Chrome browser with the configured settings.
        
        Raises:
            BrowserError: If the browser fails to start
        """
        if self._is_running and self.driver is not None:
            self._logger.warning("Browser is already running")
            return
            
        try:
            self._logger.info("Starting Chrome browser...")
            
            # Set up Chrome options
            options = ChromeOptions()
            
            # Set headless mode if specified
            if self.config.headless:
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
                
            # Add additional Chrome arguments
            for arg in self.config.chrome_arguments:
                if arg not in ["--headless", "--disable-gpu"]:  # Avoid duplicates
                    options.add_argument(arg)
                    
            # Set custom user agent if specified
            if self.config.user_agent:
                options.add_argument(f"--user-agent={self.config.user_agent}")
            
            # Set window size
            if self.config.window_size:
                options.add_argument(f"--window-size={self.config.window_size[0]},{self.config.window_size[1]}")
            else:
                options.add_argument("--start-maximized")
            
            # Additional performance and stability options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Disable automation flags detection
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Set up the Chrome service
            driver_path = self._get_chrome_driver_path()
            
            # Create Chrome service with the driver path
            self._service = ChromeService(executable_path=driver_path)
            
            # Initialize WebDriver
            self.driver = webdriver.Chrome(
                service=self._service,
                options=options
            )
            
            # Set window size if specified
            if self.config.window_size:
                self.driver.set_window_size(*self.config.window_size)
            else:
                self.driver.maximize_window()
            
            self._logger.info("Chrome browser started successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to start Chrome browser: {e}")
            if hasattr(self, '_service') and self._service:
                try:
                    self._service.stop()
                except Exception as stop_error:
                    self._logger.error(f"Error stopping Chrome service: {stop_error}")
            raise
    
    def stop(self) -> None:
        """
        Stop the Chrome browser and clean up resources.
        
        This method ensures all browser processes are properly terminated
        and resources are released.
        """
        if not self._is_running or self.driver is None:
            self._logger.warning("Browser is not running")
            return
            
        self._logger.info("Stopping Chrome browser...")
        
        try:
            # Try to close all windows and quit the browser
            if self.driver.window_handles:
                self.driver.quit()
                self._logger.debug("Browser quit successfully")
        except Exception as e:
            self._logger.error(f"Error while quitting browser: {e}")
            try:
                # Force kill if normal quit fails
                if platform.system() == 'Windows':
                    os.system('taskkill /f /im chromedriver.exe')
                    os.system('taskkill /f /im chrome.exe')
                else:
                    os.system('pkill -f chromedriver')
                    os.system('pkill -f chrome')
                self._logger.warning("Force-killed browser processes")
            except Exception as kill_error:
                self._logger.error(f"Failed to kill browser processes: {kill_error}")
        finally:
            self.driver = None
            self._is_running = False
            
        # Stop the Chrome service if it exists
        if self._service is not None:
            try:
                self._service.stop()
                self._logger.debug("Chrome service stopped")
            except Exception as e:
                self._logger.error(f"Error stopping Chrome service: {e}")
            finally:
                self._service = None
                
        self._logger.info("Browser stopped successfully")
    
    @retry_on_failure(max_retries=2, exceptions=(WebDriverException,))
    def navigate_to(self, url: str, timeout: int = 30) -> None:
        """
        Navigate to the specified URL and wait for the page to load.
        
        Args:
            url: The URL to navigate to
            timeout: Maximum time to wait for page load in seconds
            
        Raises:
            BrowserError: If browser is not initialized
            NavigationError: If navigation fails or times out
        """
        if not self.driver:
            raise BrowserNotInitializedError("Browser is not initialized")
            
        try:
            self._logger.info(f"Navigating to: {url}")
            
            # Set page load timeout
            self.driver.set_page_load_timeout(timeout)
            
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for document.readyState to be complete
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            self._logger.info(f"Successfully navigated to: {self.driver.current_url}")
            
        except TimeoutException as e:
            error_msg = f"Page load timed out after {timeout} seconds: {url}"
            self._logger.error(error_msg)
            raise NavigationError(error_msg) from e
            
        except WebDriverException as e:
            error_msg = f"Navigation failed: {e.msg if hasattr(e, 'msg') else str(e)}"
            self._logger.error(f"{error_msg} - URL: {url}")
            raise NavigationError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error during navigation to {url}: {str(e)}"
            self._logger.error(error_msg, exc_info=True)
            raise NavigationError(error_msg) from e
    
    def get_current_url(self) -> str:
        """
        Get the current URL of the active tab.
        
        Returns:
            str: The current URL
            
        Raises:
            BrowserError: If browser is not initialized or no window is open
        """
        if not self.driver:
            raise BrowserNotInitializedError("Browser is not initialized")
            
        try:
            if not self.driver.window_handles:
                raise BrowserError("No browser windows are open")
                
            return self.driver.current_url
            
        except Exception as e:
            error_msg = f"Failed to get current URL: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
            
    def get_page_source(self) -> str:
        """
        Get the current page source.
        
        Returns:
            str: The page source HTML
            
        Raises:
            BrowserError: If browser is not initialized or no window is open
        """
        if not self.driver:
            raise BrowserNotInitializedError("Browser is not initialized")
            
        try:
            if not self.driver.window_handles:
                raise BrowserError("No browser windows are open")
                
            return self.driver.page_source
            
        except Exception as e:
            error_msg = f"Failed to get page source: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def take_screenshot(self, file_path: str, full_page: bool = False) -> bool:
        """Take a screenshot of the current page.
        
        Args:
            file_path: Path to save the screenshot
            full_page: If True, capture the full page
            
        Returns:
            bool: True if screenshot was successful
        """
        if self.driver is None:
            raise BrowserError("Browser is not running")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            if full_page:
                # Scroll and capture full page
                self._logger.debug("Taking full page screenshot...")
                # Implementation for full page screenshot would go here
                # This is a simplified version
                self.driver.save_screenshot(file_path)
            else:
                # Regular viewport screenshot
                self._logger.debug(f"Taking viewport screenshot: {file_path}")
                self.driver.save_screenshot(file_path)
                
            self._logger.info(f"Screenshot saved to: {file_path}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to take screenshot: {e}")
            raise ScreenshotError(f"Failed to take screenshot: {e}")
    
    def __del__(self):
        """Ensure the browser is properly closed when the object is destroyed."""
        try:
            if self.driver is not None:
                self.stop()
        except Exception as e:
            self._logger.error(f"Error during browser cleanup: {e}")
