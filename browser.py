"""Main browser automation class for Chrome Puppet."""
import os
import time
import logging
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
from webdriver_manager.core.utils import ChromeType
from bs4 import BeautifulSoup

from .config import ChromeConfig, DEFAULT_CONFIG
from .utils import get_default_download_dir, ensure_dir, is_chrome_installed, get_chrome_version

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
        self._initialize_driver()
    
    def _initialize_driver(self) -> None:
        """Initialize the Chrome WebDriver with the configured options."""
        try:
            # Set up Chrome options
            chrome_options = self._create_chrome_options()
            
            # Set up Chrome service
            self._service = ChromeService(
                ChromeDriverManager(
                    chrome_type=self.config.chrome_type
                ).install()
            )
            
            # Initialize the WebDriver
            self.driver = webdriver.Chrome(
                service=self._service,
                options=chrome_options
            )
            
            # Set window size if specified
            if self.config.window_size:
                self.driver.set_window_size(*self.config.window_size)
                
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            self._cleanup()
            raise
    
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
