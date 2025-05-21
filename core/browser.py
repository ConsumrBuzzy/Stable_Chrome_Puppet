"""Main browser automation class for Chrome Puppet."""
import os
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Union, Tuple
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import re
from packaging import version
from bs4 import BeautifulSoup

from core.config import ChromeConfig, DEFAULT_CONFIG
from utils.utils import (
    get_default_download_dir,
    ensure_dir,
    is_chrome_installed,
    get_chrome_version,
    get_timestamp
)

logger = logging.getLogger(__name__)

class ChromePuppet:
    """A robust and extensible Chrome browser automation class."""
    
    def __init__(self, config: Optional[ChromeConfig] = None):
        """Initialize the ChromePuppet with the given configuration.
        
        Args:
            config: ChromeConfig instance with browser settings. If None, uses defaults.
        """
        self.config = config or DEFAULT_CONFIG
        self.driver: Optional[WebDriver] = None
        self._service: Optional[ChromeService] = None
        self._logger = self._setup_logging()
        self._initialize_driver()
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        # Ensure logs directory exists
        logs_dir = Path("logs")
        ensure_dir(logs_dir)
        
        # Create a logger
        logger = logging.getLogger("chrome_puppet")
        logger.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create file handler with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"chrome_puppet_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def _get_screenshot_path(self, prefix: str = "screenshot") -> Path:
        """Generate a unique screenshot file path."""
        screenshots_dir = Path("screenshots")
        ensure_dir(screenshots_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return screenshots_dir / f"{prefix}_{timestamp}.png"

    def take_screenshot(self, prefix: str = "screenshot") -> Optional[Path]:
        """Take a screenshot and save it to the screenshots directory.
        
        Args:
            prefix: Prefix for the screenshot filename
            
        Returns:
            Path to the saved screenshot or None if failed
        """
        if not self.driver:
            self._logger.warning("Cannot take screenshot: No active WebDriver")
            return None
            
        try:
            screenshot_path = self._get_screenshot_path(prefix)
            self.driver.save_screenshot(str(screenshot_path))
            self._logger.info(f"Screenshot saved to {screenshot_path}")
            return screenshot_path
        except Exception as e:
            self._logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def _get_chrome_version(self) -> str:
        """Get the installed Chrome version."""
        try:
            if os.name == 'nt':  # Windows
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  r'Software\Google\Chrome\BLBeacon') as key:
                    version = winreg.QueryValueEx(key, 'version')[0]
            else:  # macOS and Linux
                import subprocess
                if os.path.exists('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'):
                    # macOS
                    cmd = '/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version'
                else:
                    # Linux
                    cmd = 'google-chrome --version' if shutil.which('google-chrome') else 'chromium --version'
                version = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
                version = re.search(r'\d+\.\d+\.\d+', version).group()
            return version
        except Exception as e:
            self._logger.warning(f"Could not detect Chrome version: {e}")
            return '114.0.0.0'  # Fallback to a common version

    def _initialize_driver(self):
        """Initialize the Chrome WebDriver with the specified configuration."""
        try:
            self._logger.info("Initializing Chrome WebDriver...")
            
            # Set up Chrome options
            chrome_options = ChromeOptions()
            
            # Set headless mode if specified
            if self.config.headless:
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--disable-gpu")
            
            # Add additional arguments
            for arg in self.config.chrome_arguments:
                chrome_options.add_argument(arg)
            
            # Configure ChromeDriver manager
            self._logger.info("Setting up ChromeDriver...")
            
            # Get the appropriate Chrome type
            chrome_type = ChromeType.CHROMIUM if self.config.chromium else ChromeType.GOOGLE
            
            # Set up Chrome service with specific driver version
            self._service = ChromeService(
                ChromeDriverManager(
                    chrome_type=chrome_type,
                    version='114.0.5735.90'  # Stable version known to work well
                ).install()
            )
            
            # Initialize WebDriver with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver = webdriver.Chrome(
                        service=self._service,
                        options=chrome_options
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    self._logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    time.sleep(2)  # Wait before retry
            
            # Set window size if specified
            if self.config.window_size:
                self.driver.set_window_size(*self.config.window_size)
            else:
                self.driver.maximize_window()
            
            self._logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to initialize Chrome WebDriver: {str(e)}")
            raise
    
    def navigate_to(self, url: str, wait_time: Optional[int] = None) -> bool:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            wait_time: Time in seconds to wait for page load. If None, uses config value.
            
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        try:
            # Clean the URL
            url = url.strip()
            
            # Simple URL formatting - just add https:// if no scheme is present
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            self._logger.info(f"Attempting to navigate to: {url}")
            
            # Set a reasonable page load timeout
            wait = wait_time or self.config.implicit_wait
            self.driver.set_page_load_timeout(wait)
            
            # Try to navigate to the URL
            try:
                self.driver.get(url)
                self._logger.info("Page load command sent successfully")
            except Exception as e:
                self._logger.error(f"Error during driver.get(): {str(e)}")
                raise
            
            # Wait for the page to load completely
            try:
                WebDriverWait(self.driver, wait).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                self._logger.info("Page loaded successfully")
            except Exception as e:
                self._logger.warning(f"Page load check warning: {str(e)}")
                # Continue even if the readyState check fails
            
            # Take a screenshot to verify the page loaded
            screenshot_path = self.take_screenshot("page_loaded")
            if screenshot_path:
                self._logger.info(f"Screenshot saved to: {screenshot_path}")
            
            # Get the current URL for verification
            current_url = self.driver.current_url
            self._logger.info(f"Current URL: {current_url}")
            
            # Get the page title
            try:
                title = self.driver.title
                self._logger.info(f"Page title: {title}")
            except Exception as e:
                self._logger.warning(f"Could not get page title: {str(e)}")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Navigation failed: {str(e)}", exc_info=True)
            # Take a screenshot on error
            error_screenshot = self.take_screenshot("navigation_error")
            if error_screenshot:
                self._logger.info(f"Error screenshot saved to: {error_screenshot}")
            return False
    
    def quit(self):
        """Close the browser and clean up resources."""
        try:
            if self.driver:
                self._logger.info("Closing browser...")
                self.driver.quit()
                self.driver = None
            if self._service:
                self._service.stop()
                self._service = None
            self._logger.info("Browser closed")
        except Exception as e:
            self._logger.error(f"Error while closing browser: {e}")
    
    def _create_chrome_options(self) -> ChromeOptions:
        """Create and configure Chrome options based on the config."""
        options = ChromeOptions()
        
        # Set headless mode if specified
        if self.config.headless:
            options.add_argument("--headless=new")
        
        # Add common arguments
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set user agent
        if self.config.user_agent:
            options.add_argument(f"user-agent={self.config.user_agent}")
        
        # Set download directory if specified
        if self.config.download_dir:
            ensure_dir(self.config.download_dir)
            prefs = {
                "download.default_directory": self.config.download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            options.add_experimental_option("prefs", prefs)
        
        # Add any additional Chrome arguments
        for arg in self.config.chrome_arguments:
            options.add_argument(arg)
        
        # Add any extensions
        for ext in self.config.extensions:
            if os.path.exists(ext):
                options.add_extension(ext)
            else:
                logger.warning(f"Extension not found: {ext}")
        
        # Set Chrome binary location if specified
        if self.config.chrome_path and os.path.isfile(self.config.chrome_path):
            options.binary_location = self.config.chrome_path
        
        return options
    
    def get(self, url: str, wait_time: Optional[int] = None) -> None:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to.
            wait_time: Time to wait for page load in seconds. If None, uses config timeout.
        """
        if not self.driver:
            raise RuntimeError("WebDriver is not initialized")
        
        try:
            self.driver.get(url)
            logger.info(f"Navigated to: {url}")
            
            # Wait for page to load
            if wait_time is None:
                wait_time = self.config.timeout
                
            time.sleep(min(2, wait_time))  # Quick initial wait
            
            # Wait for document.readyState to be complete
            WebDriverWait(self.driver, wait_time).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Additional wait for dynamic content
            time.sleep(0.5)
            
        except TimeoutException:
            logger.warning(f"Page load timed out after {wait_time} seconds: {url}")
        except WebDriverException as e:
            logger.error(f"Error navigating to {url}: {e}")
            raise
    
    def get_soup(self, url: Optional[str] = None) -> Optional[BeautifulSoup]:
        """Get the page source as a BeautifulSoup object.
        
        Args:
            url: Optional URL to navigate to before getting the page source.
                If None, uses the current page.
                
        Returns:
            BeautifulSoup object or None if an error occurs.
        """
        if not self.driver:
            logger.error("WebDriver is not initialized")
            return None
            
        try:
            if url:
                self.get(url)
                
            page_source = self.driver.page_source
            return BeautifulSoup(page_source, 'html.parser')
            
        except Exception as e:
            logger.error(f"Error getting page source: {e}")
            return None
    
    def close(self) -> None:
        """Close the browser and clean up resources."""
        self._cleanup()
        
    def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
        finally:
            self.driver = None
            
        try:
            if self._service:
                self._service.stop()
        except Exception as e:
            logger.error(f"Error stopping Chrome service: {e}")
        finally:
            self._service = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure resources are cleaned up."""
        self.close()
        
    def __del__(self):
        """Destructor - ensure resources are cleaned up."""
        self.close()
