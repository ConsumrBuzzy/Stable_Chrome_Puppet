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

# Third-party imports
try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

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
        # Try to find ChromeDriver in common locations
        common_paths = [
            "chromedriver",
            "chromedriver.exe",
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver",
            "C:\\chromedriver\\chromedriver.exe",
            str(Path.home() / "chromedriver" / "chromedriver.exe")
        ]
        
        # Check common paths first
        for path in common_paths:
            if os.path.exists(path):
                self._logger.info(f"Found ChromeDriver at: {path}")
                return path
        
        # Try webdriver-manager if available
        if ChromeDriverManager is not None:
            try:
                driver_path = ChromeDriverManager().install()
                self._logger.info(f"Using ChromeDriver from webdriver-manager: {driver_path}")
                return driver_path
            except Exception as e:
                self._logger.warning(f"Failed to install ChromeDriver: {e}")
        
        # If we get here, we couldn't find ChromeDriver
        error_msg = (
            "Could not find ChromeDriver. Please ensure it's installed and in your PATH, "
            "or install webdriver-manager with: pip install webdriver-manager"
        )
        self._logger.error(error_msg)
        raise BrowserError(error_msg)
        
        # Fallback to common locations
        chromedriver_name = 'chromedriver.exe' if os.name == 'nt' else 'chromedriver'
        is_64bit = sys.maxsize > 2**32
        
        # Check common locations
        common_paths = [
            os.path.join(os.path.dirname(__file__), 'bin', chromedriver_name),
            os.path.join(os.path.expanduser('~'), '.wdm', 'drivers', 'chromedriver', 
                         'win64' if is_64bit else 'win32', chromedriver_name),
            os.path.join(os.path.expanduser('~'), '.wdm', 'drivers', 'chromedriver', 'mac64', chromedriver_name),
            os.path.join(os.path.expanduser('~'), '.wdm', 'drivers', 'chromedriver', 'linux64', chromedriver_name),
            'chromedriver',
            '/usr/local/bin/chromedriver',
            '/usr/bin/chromedriver',
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'ChromeDriver', chromedriver_name),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'ChromeDriver', chromedriver_name)
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                self._logger.info(f"Found ChromeDriver at: {path}")
                return path
        
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
                options=chrome_options
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
        """Stop the Chrome browser."""
        if self.driver is None:
            self._logger.warning("Browser is not running")
            return
        
        self._logger.info("Stopping Chrome browser...")
        
        try:
            self.driver.quit()
            self._logger.info("Chrome browser stopped successfully")
        except Exception as e:
            self._logger.error(f"Error while stopping browser: {e}")
            raise
        finally:
            self.driver = None
            self._service = None
    
    @retry_on_failure(max_retries=2, exceptions=(WebDriverException,))
    def navigate_to(self, url: str, wait_time: Optional[float] = None) -> bool:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            wait_time: Optional time to wait for page load (uses config value if None)
            
        Returns:
            bool: True if navigation was successful
        """
        if self.driver is None:
            raise BrowserError("Browser is not running")
        
        try:
            self._logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            wait = wait_time or self.config.implicit_wait
            if wait > 0:
                self.driver.set_page_load_timeout(wait)
                self._logger.debug(f"Waiting up to {wait} seconds for page load...")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to navigate to {url}: {e}")
            raise NavigationError(f"Failed to navigate to {url}: {e}")
    
    def get_page_source(self) -> str:
        """Get the current page source."""
        if self.driver is None:
            raise BrowserError("Browser is not running")
        return self.driver.page_source
    
    def get_current_url(self) -> str:
        """Get the current URL."""
        if self.driver is None:
            raise BrowserError("Browser is not running")
        return self.driver.current_url
    
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
