"""
ChromePuppet - High-level browser automation interface.

This module provides the main ChromePuppet class that serves as the primary interface
for browser automation tasks, wrapping the lower-level browser functionality.
"""
import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

from .chrome import ChromeBrowser
from ..config import ChromeConfig
from .exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError,
    ElementNotFoundError,
    ScreenshotError
)

class ChromePuppet:
    """
    High-level interface for browser automation.
    
    This class provides a user-friendly API for common browser automation tasks,
    handling the underlying browser instance and providing convenient methods.
    """
    
    def __init__(self, config: Optional[ChromeConfig] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the ChromePuppet with the given configuration.
        
        Args:
            config: Chrome configuration. If None, uses default settings.
            logger: Logger instance. If None, creates a default logger.
        """
        self._config = config or ChromeConfig()
        self._logger = logger or logging.getLogger(__name__)
        self._browser: Optional[ChromeBrowser] = None
        self._is_running = False
    
    def start(self) -> None:
        """
        Start the browser session.
        
        Raises:
            BrowserError: If the browser fails to start
        """
        if self._is_running and self._browser is not None:
            self._logger.warning("Browser is already running")
            return
            
        try:
            self._logger.info("Starting Chrome browser...")
            self._browser = ChromeBrowser(self._config, self._logger)
            self._browser.start()
            self._is_running = True
            self._logger.info("Chrome browser started successfully")
        except Exception as e:
            self._is_running = False
            error_msg = f"Failed to start browser: {e}"
            self._logger.error(error_msg, exc_info=True)
            raise BrowserError(error_msg) from e
    
    def stop(self) -> None:
        """
        Stop the browser session and clean up resources.
        """
        if not self._is_running or self._browser is None:
            self._logger.warning("Browser is not running")
            return
            
        try:
            self._logger.info("Stopping Chrome browser...")
            self._browser.stop()
            self._logger.info("Chrome browser stopped successfully")
        except Exception as e:
            self._logger.error(f"Error while stopping browser: {e}", exc_info=True)
            raise
        finally:
            self._is_running = False
            self._browser = None
    
    def navigate_to(self, url: str, timeout: int = 30) -> None:
        """
        Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            timeout: Maximum time to wait for page load in seconds
            
        Raises:
            BrowserError: If browser is not initialized
            NavigationError: If navigation fails or times out
        """
        if not self._is_running or self._browser is None:
            raise BrowserNotInitializedError("Browser is not running")
            
        try:
            self._browser.navigate_to(url, timeout)
        except Exception as e:
            error_msg = f"Failed to navigate to {url}: {e}"
            self._logger.error(error_msg, exc_info=True)
            raise NavigationError(error_msg) from e
    
    def get_current_url(self) -> str:
        """
        Get the current URL.
        
        Returns:
            str: The current URL
            
        Raises:
            BrowserError: If browser is not initialized
        """
        if not self._is_running or self._browser is None:
            raise BrowserNotInitializedError("Browser is not running")
            
        return self._browser.get_current_url()
    
    def get_page_source(self) -> str:
        """
        Get the current page source.
        
        Returns:
            str: The page source HTML
            
        Raises:
            BrowserError: If browser is not initialized
        """
        if not self._is_running or self._browser is None:
            raise BrowserNotInitializedError("Browser is not running")
            
        return self._browser.get_page_source()
    
    def take_screenshot(self, file_path: str, full_page: bool = False) -> bool:
        """
        Take a screenshot of the current page.
        
        Args:
            file_path: Path to save the screenshot
            full_page: Whether to capture the full page (may not work in headless mode)
            
        Returns:
            bool: True if screenshot was saved successfully
            
        Raises:
            BrowserError: If browser is not initialized or screenshot fails
        """
        if not self._is_running or self._browser is None:
            raise BrowserNotInitializedError("Browser is not running")
            
        try:
            return self._browser.take_screenshot(file_path, full_page)
        except Exception as e:
            error_msg = f"Failed to take screenshot: {e}"
            self._logger.error(error_msg, exc_info=True)
            raise ScreenshotError(error_msg) from e
    
    def execute_script(self, script: str, *args) -> Any:
        """
        Execute JavaScript in the current page context.
        
        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script
            
        Returns:
            The script's return value
            
        Raises:
            BrowserError: If browser is not initialized or script execution fails
        """
        if not self._is_running or self._browser is None:
            raise BrowserNotInitializedError("Browser is not running")
            
        try:
            return self._browser.driver.execute_script(script, *args)
        except Exception as e:
            error_msg = f"JavaScript execution failed: {e}"
            self._logger.error(error_msg, exc_info=True)
            raise BrowserError(error_msg) from e
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False  # Don't suppress exceptions
    
    @property
    def is_running(self) -> bool:
        """Check if the browser is running."""
        return self._is_running and self._browser is not None
    
    @property
    def browser(self) -> ChromeBrowser:
        """Get the underlying browser instance."""
        if self._browser is None:
            raise BrowserNotInitializedError("Browser is not running")
        return self._browser
