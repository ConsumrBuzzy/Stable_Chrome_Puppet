"""
Chrome browser implementation using Selenium WebDriver.
"""
import logging
import os
from typing import Optional, Tuple, Union

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager

from core.browser import Browser
from core.config import ChromeConfig

logger = logging.getLogger(__name__)

class ChromeBrowser(Browser):
    """Chrome browser implementation."""
    
    def __init__(self, config: Optional[ChromeConfig] = None):
        """Initialize Chrome browser with the given configuration.
        
        Args:
            config: Chrome configuration. If None, default settings will be used.
        """
        self.config = config or ChromeConfig()
        self._driver: Optional[ChromeWebDriver] = None
        self._init_driver()
    
    def _init_driver(self) -> None:
        """Initialize the Chrome WebDriver with the configured options."""
        chrome_options = self._create_chrome_options()
        
        try:
            # Try to use the installed ChromeDriver first
            self._driver = webdriver.Chrome(
                service=ChromeService(),
                options=chrome_options
            )
        except WebDriverException as e:
            logger.warning("Failed to use installed ChromeDriver, falling back to webdriver-manager: %s", e)
            # Fall back to webdriver-manager if ChromeDriver not found
            self._driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=chrome_options
            )
        
        # Configure timeouts
        self._driver.set_page_load_timeout(self.config.page_load_timeout)
        self._driver.set_script_timeout(self.config.script_timeout)
        
        if self.config.implicit_wait > 0:
            self._driver.implicitly_wait(self.config.implicit_wait)
    
    def _create_chrome_options(self) -> ChromeOptions:
        """Create ChromeOptions based on the configuration."""
        options = ChromeOptions()
        
        # Basic options
        if self.config.headless:
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
        
        # Window size
        width, height = self.config.get_window_size()
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
        
        return options
    
    def get(self, url: str) -> None:
        """Navigate to the specified URL."""
        if not self._driver:
            raise RuntimeError("Browser is not initialized")
        self._driver.get(url)
    
    @property
    def title(self) -> str:
        """Get the current page title."""
        if not self._driver:
            raise RuntimeError("Browser is not initialized")
        return self._driver.title
    
    @property
    def current_url(self) -> str:
        """Get the current URL."""
        if not self._driver:
            raise RuntimeError("Browser is not initialized")
        return self._driver.current_url
    
    def execute_script(self, script: str, *args) -> object:
        """Execute JavaScript in the current page context."""
        if not self._driver:
            raise RuntimeError("Browser is not initialized")
        return self._driver.execute_script(script, *args)
    
    def close(self) -> None:
        """Close the browser and release resources."""
        if self._driver:
            try:
                self._driver.quit()
            except Exception as e:
                logger.warning("Error while closing browser: %s", e)
            finally:
                self._driver = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
