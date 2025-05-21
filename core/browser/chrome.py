"""Chrome browser implementation."""
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Tuple, Callable

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

# Third-party imports
from webdriver_manager.chrome import ChromeDriverManager

# Local imports
from .base import BaseBrowser, retry_on_failure
from .exceptions import BrowserError, NavigationError, ScreenshotError
from ..config import ChromeConfig

class ChromeBrowser(BaseBrowser):
    """Chrome browser implementation using Selenium WebDriver."""
    
    def __init__(self, config: ChromeConfig, logger=None):
        """Initialize the Chrome browser.
        
        Args:
            config: Chrome configuration object
            logger: Optional logger instance
        """
        super().__init__(config, logger)
        self.config = config
        self.driver: Optional[WebDriver] = None
        self._service = None
    
    def _get_chrome_driver_path(self) -> str:
        """Get the path to the ChromeDriver executable."""
        try:
            # First try to use webdriver-manager to get the correct ChromeDriver
            driver_path = ChromeDriverManager().install()
            self._logger.info(f"Using ChromeDriver from webdriver-manager: {driver_path}")
            return driver_path
            
        except Exception as e:
            self._logger.warning(f"Failed to get ChromeDriver from webdriver-manager: {e}")
            
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
            
            raise BrowserError(
                "Could not find or download ChromeDriver. "
                f"System: {platform.system()} {platform.machine()} (64-bit: {is_64bit})\n"
                "Please ensure it's installed and in your PATH, or install it manually from "
                "https://chromedriver.chromium.org/downloads"
            )
    
    @retry_on_failure(max_retries=3, delay=2, backoff=2, exceptions=(WebDriverException,))
    def start(self) -> None:
        """Start the Chrome browser."""
        if self.driver is not None:
            self._logger.warning("Browser is already running")
            return
        
        self._logger.info("Starting Chrome browser...")
        
        try:
            # Set up Chrome options
            chrome_options = ChromeOptions()
            
            # Set headless mode if specified
            if self.config.headless:
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--disable-gpu")
            
            # Add additional arguments
            for arg in self.config.chrome_arguments:
                if arg not in ["--headless", "--disable-gpu"]:  # Avoid duplicates
                    chrome_options.add_argument(arg)
            
            # Add common arguments for stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Disable automation flags that might trigger bot detection
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Get ChromeDriver path
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
