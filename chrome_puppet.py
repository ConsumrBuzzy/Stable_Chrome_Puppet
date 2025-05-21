"""
Chrome Puppet - A robust and extensible Chrome browser automation tool.

This module provides the main ChromePuppet class for browser automation tasks.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from core.config import ChromeConfig, DEFAULT_CONFIG
from core.utils import (
    ensure_dir,
    ensure_file,
    get_chrome_version,
    get_default_download_dir,
    get_timestamp,
    is_chrome_installed,
    retry,
    setup_logger
)

logger = logging.getLogger(__name__)

class ChromePuppet:
    """Main class for Chrome browser automation."""
    
    def __init__(self, config: Optional[ChromeConfig] = None) -> None:
        """Initialize ChromePuppet with the given configuration.
        
        Args:
            config: Configuration object for ChromePuppet. If None, uses DEFAULT_CONFIG.
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
        timestamp = get_timestamp()
        log_file = logs_dir / f"chrome_puppet_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(
            logging.DEBUG if self.config.verbose else logging.INFO
        )
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _get_screenshot_path(self, prefix: str = "screenshot") -> Path:
        """Generate a unique screenshot file path.
        
        Args:
            prefix: Prefix for the screenshot filename
            
        Returns:
            Path object for the screenshot
        """
        screenshots_dir = Path("screenshots")
        ensure_dir(screenshots_dir)
        timestamp = get_timestamp()
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
    
    def _create_chrome_options(self) -> ChromeOptions:
        """Create and configure ChromeOptions based on the config."""
        options = ChromeOptions()
        
        # Set headless mode if specified
        if self.config.headless:
            options.add_argument("--headless=new")
        
        # Set window size
        if self.config.window_size:
            width, height = self.config.window_size
            options.add_argument(f"--window-size={width},{height}")
        
        # Add other options
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Set user agent if specified
        if self.config.user_agent:
            options.add_argument(f"user-agent={self.config.user_agent}")
        
        # Set download directory if specified
        if self.config.download_dir:
            prefs = {
                "download.default_directory": str(self.config.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            options.add_experimental_option("prefs", prefs)
        
        return options
    
    def _initialize_driver(self) -> None:
        """Initialize the Chrome WebDriver with the configured options."""
        try:
            self._logger.info("Initializing Chrome WebDriver...")
            
            # Set up Chrome options
            chrome_options = self._create_chrome_options()
            
            # Set up Chrome service
            self._logger.debug("Setting up ChromeDriver...")
            self._service = ChromeService(
                ChromeDriverManager(
                    chrome_type=self.config.chrome_type
                ).install()
            )
            
            # Initialize the WebDriver
            self._logger.debug("Initializing WebDriver...")
            self.driver = webdriver.Chrome(
                service=self._service,
                options=chrome_options
            )
            
            # Set implicit wait if specified
            if self.config.implicit_wait > 0:
                self.driver.implicitly_wait(self.config.implicit_wait)
            
            self._logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to initialize Chrome WebDriver: {e}", exc_info=True)
            self._cleanup()
            raise
    
    def get(self, url: str) -> None:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
        """
        if not self.driver:
            self._logger.error("Cannot navigate: WebDriver not initialized")
            raise RuntimeError("WebDriver not initialized")
        
        self._logger.info(f"Navigating to: {url}")
        self.driver.get(url)
    
    @property
    def title(self) -> str:
        """Get the current page title."""
        if not self.driver:
            self._logger.warning("Cannot get title: WebDriver not initialized")
            return ""
        return self.driver.title
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                self._logger.info("WebDriver closed")
            except Exception as e:
                self._logger.error(f"Error closing WebDriver: {e}", exc_info=True)
            finally:
                self.driver = None
        
        if self._service:
            try:
                self._service.stop()
            except Exception as e:
                self._logger.error(f"Error stopping Chrome service: {e}", exc_info=True)
            finally:
                self._service = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - ensure resources are cleaned up."""
        self._cleanup()


if __name__ == "__main__":
    # Example usage
    with ChromePuppet() as browser:
        browser.get("https://www.google.com")
        print(f"Page title: {browser.title}")
