"""Chrome browser implementation."""
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Union

from selenium.webdriver import Chrome as SeleniumChrome
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

from ....config import ChromeConfig
from ....types import BrowserType, WindowSize
from ...base_driver import BaseDriver

logger = logging.getLogger(__name__)
T = TypeVar('T', bound='ChromeBrowser')


class ChromeBrowser(BaseDriver[T]):
    """Chrome browser implementation using Selenium WebDriver."""
    
    def __init__(self, config: Optional[ChromeConfig] = None) -> None:
        """Initialize the Chrome browser.
        
        Args:
            config: Configuration for the browser instance.
        """
        super().__init__(config or ChromeConfig())
        self._driver: Optional[SeleniumChrome] = None
        self._service: Optional[ChromeService] = None
        self._options: Optional[ChromeOptions] = None
        self._is_running: bool = False  # Ensure this is initialized
    
    def start(self) -> T:
        """Start the Chrome browser instance.
        
        Returns:
            Self for method chaining.
            
        Raises:
            WebDriverException: If the browser fails to start.
        """
        if self._is_running:
            logger.warning("Browser is already running")
            return self
            
        try:
            self._options = self._setup_options()
            self._service = self._create_service()
            
            logger.info("Starting Chrome browser")
            self._driver = SeleniumChrome(
                service=self._service,
                options=self._options
            )
            
            self._is_running = True
            logger.info("Chrome browser started successfully")
            return self
            
        except Exception as e:
            logger.error(f"Failed to start Chrome browser: {e}")
            self.stop()
            raise
    
    def stop(self) -> None:
        """Stop the Chrome browser and clean up resources."""
        if not getattr(self, '_is_running', False):
            return
            
        try:
            if hasattr(self, '_driver') and self._driver is not None:
                try:
                    self._driver.quit()
                except Exception as e:
                    logger.error(f"Error while quitting driver: {e}")
                finally:
                    self._driver = None
                
            if hasattr(self, '_service') and self._service is not None:
                try:
                    self._service.stop()
                except Exception as e:
                    logger.error(f"Error while stopping service: {e}")
                finally:
                    self._service = None
                
            self._is_running = False
            logger.info("Chrome browser stopped")
            
        except Exception as e:
            self._is_running = False
            logger.error(f"Error while stopping Chrome browser: {e}")
            raise
    
    def get_browser_type(self) -> BrowserType:
        """Get the browser type.
        
        Returns:
            The browser type (CHROME).
        """
        return BrowserType.CHROME
    
    def get_options(self) -> ChromeOptions:
        """Get the Chrome options.
        
        Returns:
            The Chrome options instance.
            
        Raises:
            RuntimeError: If the browser is not started.
        """
        if not self._options:
            self._options = self._setup_options()
        return self._options
    
    def get_service(self) -> ChromeService:
        """Get the Chrome service instance.
        
        Returns:
            The Chrome service instance.
            
        Raises:
            RuntimeError: If the browser is not started.
        """
        if not self._service:
            self._service = self._create_service()
        return self._service
    
    def _setup_options(self) -> ChromeOptions:
        """Set up Chrome options based on configuration.
        
        Returns:
            Configured ChromeOptions instance.
        """
        options = ChromeOptions()
        
        # Set headless mode
        if self.config.headless:
            options.add_argument("--headless=new")
        
        # Set window size
        if self.config.window_size:
            options.add_argument(f"--window-size={self.config.window_size.width},{self.config.window_size.height}")
        
        # Set user agent if provided
        if self.config.user_agent:
            options.add_argument(f"--user-agent={self.config.user_agent}")
        
        # Add additional arguments from config
        for arg in self.config.extra_args or []:
            options.add_argument(arg)
        
        # Set experimental options
        if self.config.experimental_options:
            for key, value in self.config.experimental_options.items():
                options.set_capability(key, value)
        
        return options
    
    def _create_service(self) -> ChromeService:
        """Create and configure the Chrome service.
        
        Returns:
            Configured ChromeService instance.
        """
        service_args = self.config.service_args or []
        service_log_path = self.config.service_log_path or "chromedriver.log"
        
        service = ChromeService(
            executable_path=self.config.driver_path,
            service_args=service_args,
            log_path=service_log_path
        )
        
        return service
    
    @property
    def driver(self) -> SeleniumChrome:
        """Get the Selenium WebDriver instance.
        
        Returns:
            The Selenium Chrome WebDriver instance.
            
        Raises:
            RuntimeError: If the browser is not started.
        """
        if not self._driver:
            raise RuntimeError("Browser is not running. Call start() first.")
        return self._driver
