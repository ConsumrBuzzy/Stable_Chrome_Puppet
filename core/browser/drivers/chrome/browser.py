"""Chrome browser implementation."""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Type, TypeVar, Generic, TYPE_CHECKING

from selenium import webdriver
from selenium.common.exceptions import (
    NoAlertPresentException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.shadowroot import ShadowRoot

from core.browser.base import BaseBrowser
from core.config.base import BrowserConfig
from core.browser.exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError,
    ScreenshotError,
)

if TYPE_CHECKING:
    from selenium.webdriver.remote.shadowroot import ShadowRoot

T = TypeVar('T', bound='ChromeBrowser')

# Type aliases
TimeoutType = Union[float, int]
ElementType = Union[WebElement, ShadowRoot]
LocatorType = tuple[str, str]

from core.browser.drivers.chrome.config import ChromeConfig
from core.browser.drivers.chrome.options import ChromeOptionsBuilder
from core.browser.drivers.chrome.service import ChromeServiceFactory

# Logger will be set in __init__

class ChromeBrowser(BaseBrowser):
    """Chrome browser implementation using Selenium WebDriver."""
    
    def __init__(self, config: Optional[ChromeConfig] = None, logger: Optional[logging.Logger] = None) -> None:
        """Initialize the Chrome browser.
        
        Args:
            config: Configuration for the browser instance.
            logger: Logger instance to use.
        """
        # Ensure we have a config
        if config is None:
            config = ChromeConfig()
            
        # Initialize the base browser
        super().__init__(config, logger)
        
        # Set up logger if not provided
        if logger is None:
            self._logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize instance variables
        self._driver: Optional[ChromeWebDriver] = None
        self._service: Optional[ChromeService] = None
        self._options: Optional[ChromeOptions] = None
        self._is_running: bool = False
        self._config = config  # Store the config for later use
    
    def navigate_to(self, url: str, wait_time: Optional[float] = None) -> bool:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            wait_time: Optional time to wait for page load
            
        Returns:
            bool: True if navigation was successful, False otherwise
            
        Raises:
            BrowserNotInitializedError: If the browser is not running
            NavigationError: If navigation fails
        """
        self._check_browser_initialized()
        
        try:
            self._logger.info(f"Navigating to {url}")
            
            # Set page load timeout if specified
            if wait_time is not None:
                self._driver.set_page_load_timeout(wait_time)
            
            self._driver.get(url)
            self._logger.info(f"Successfully navigated to {url}")
            return True
            
        except TimeoutException as e:
            error_msg = f"Timeout while navigating to {url}: {e}"
            self._logger.error(error_msg)
            raise NavigationError(error_msg) from e
            
        except WebDriverException as e:
            error_msg = f"Failed to navigate to {url}: {e}"
            self._logger.error(error_msg)
            raise NavigationError(error_msg) from e
            
    def start(self) -> 'ChromeBrowser':
        """Start the Chrome browser instance.
        
        Returns:
            Self for method chaining.
            
        Raises:
            BrowserError: If the browser fails to start.
        """
        if self._is_running:
            self._logger.warning("Browser is already running")
            return self
            
        try:
            # Initialize Chrome options
            try:
                options_builder = ChromeOptionsBuilder(self._config)
                self._options = options_builder.build()
                self._logger.debug("Successfully built Chrome options")
            except Exception as e:
                error_msg = f"Failed to build Chrome options: {e}"
                self._logger.error(error_msg)
                raise BrowserError(error_msg) from e
            
            # Create Chrome service
            try:
                service_factory = ChromeServiceFactory(self._config)
                self._service = service_factory.create_service()
                self._logger.debug("Successfully created Chrome service")
            except Exception as e:
                error_msg = f"Failed to create Chrome service: {e}"
                self._logger.error(error_msg)
                raise BrowserError(error_msg) from e
            
            self._logger.info("Starting Chrome browser")
            try:
                # Log the options being used
                self._logger.debug(f"Chrome options: {self._options.arguments}")
                if hasattr(self._service, 'service_url'):
                    self._logger.debug(f"Chrome service URL: {self._service.service_url}")
                
                # Create the WebDriver instance
                self._driver = ChromeWebDriver(
                    service=self._service,
                    options=self._options
                )
                
                # Mark as running after successful driver creation
                self._is_running = True
                self._logger.info("Chrome WebDriver initialized successfully")
                
                # Set window size if specified
                if hasattr(self._config, 'window_size') and self._config.window_size:
                    try:
                        self._logger.debug(f"Setting window size to: {self._config.window_size}")
                        self.set_window_size(*self._config.window_size)
                    except Exception as e:
                        self._logger.warning(f"Could not set window size: {e}")
                
                self._logger.info("Chrome browser started successfully")
                return self
                
            except Exception as e:
                self._is_running = False
                error_msg = f"Failed to initialize Chrome WebDriver: {str(e)}"
                self._logger.error(error_msg, exc_info=True)
                
                # Try to clean up resources
                if self._driver is not None:
                    try:
                        self._driver.quit()
                    except Exception as quit_error:
                        self._logger.error(f"Error while cleaning up WebDriver: {quit_error}")
                    finally:
                        self._driver = None
                
                # Provide more detailed error information
                if "This version of ChromeDriver only supports Chrome version" in str(e):
                    error_msg += "\n\nIt seems there's a version mismatch between Chrome and ChromeDriver. " \
                               "Please ensure you have compatible versions installed."
                
                raise BrowserError(error_msg) from e
            
        except WebDriverException as e:
            error_msg = f"WebDriver error while starting Chrome: {e}"
            self._logger.error(error_msg, exc_info=True)
            self.stop()
            raise BrowserError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error starting Chrome browser: {e}"
            self._logger.error(error_msg, exc_info=True)
            self.stop()
            raise BrowserError(error_msg) from e
    
    def stop(self) -> None:
        """Stop the Chrome browser and clean up resources.
        
        This method ensures all browser processes and resources are properly cleaned up.
        """
        if not self._is_running:
            self._logger.debug("Browser is not running, nothing to stop")
            return
            
        try:
            self._logger.info("Stopping Chrome browser")
            
            # Close all browser windows and end the WebDriver session
            if self._driver is not None:
                try:
                    self._driver.quit()
                except WebDriverException as e:
                    self._logger.warning(f"Error while quitting WebDriver: {e}")
                except Exception as e:
                    self._logger.error(f"Unexpected error while quitting WebDriver: {e}", exc_info=True)
                finally:
                    self._driver = None
            
            # Stop the Chrome service
            if self._service is not None:
                try:
                    self._service.stop()
                except Exception as e:
                    self._logger.error(f"Error while stopping Chrome service: {e}", exc_info=True)
                finally:
                    self._service = None
            
            self._is_running = False
            self._logger.info("Chrome browser stopped successfully")
            
        except Exception as e:
            self._is_running = False
            self._logger.error(f"Unexpected error while stopping Chrome browser: {e}", exc_info=True)
            raise BrowserError(f"Failed to stop Chrome browser: {e}") from e
    
    # Navigation Methods
    
    def get(self, url: str, timeout: Optional[float] = None) -> None:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to.
            timeout: Maximum time in seconds to wait for page load. If None, uses default timeout.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            NavigationError: If navigation fails.
        """
        if not self._is_running or self._driver is None:
            raise BrowserNotInitializedError("Browser is not running")
            
        try:
            self._logger.info(f"Navigating to: {url}")
            if timeout is not None:
                self._driver.set_page_load_timeout(timeout)
                
            self._driver.get(url)
            self._logger.debug(f"Successfully navigated to: {url}")
            
        except WebDriverException as e:
            error_msg = f"Failed to navigate to {url}: {e}"
            self._logger.error(error_msg)
            raise NavigationError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error during navigation to {url}: {e}"
            self._logger.error(error_msg, exc_info=True)
            raise NavigationError(error_msg) from e
    
    def back(self) -> None:
        """Go back to the previous page in browser history.
        
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            NavigationError: If the back operation fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug("Navigating back in browser history")
            self._driver.back()
            self._logger.debug("Successfully navigated back")
            
        except WebDriverException as e:
            error_msg = f"Failed to navigate back: {e}"
            self._logger.error(error_msg)
            raise NavigationError(error_msg) from e
    
    def forward(self) -> None:
        """Go forward to the next page in browser history.
        
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            NavigationError: If the forward operation fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug("Navigating forward in browser history")
            self._driver.forward()
            self._logger.debug("Successfully navigated forward")
            
        except WebDriverException as e:
            error_msg = f"Failed to navigate forward: {e}"
            self._logger.error(error_msg)
            raise NavigationError(error_msg) from e
    
    def refresh(self) -> None:
        """Refresh the current page.
        
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            NavigationError: If the refresh operation fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug("Refreshing current page")
            self._driver.refresh()
            self._logger.debug("Successfully refreshed page")
            
        except WebDriverException as e:
            error_msg = f"Failed to refresh page: {e}"
            self._logger.error(error_msg)
            raise NavigationError(error_msg) from e
    
    # Window Management
    
    def set_window_size(self, width: int, height: int) -> None:
        """Set the browser window size.
        
        Args:
            width: Window width in pixels.
            height: Window height in pixels.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            BrowserError: If setting window size fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug(f"Setting window size to {width}x{height}")
            self._driver.set_window_size(width, height)
            self._logger.debug(f"Window size set to {width}x{height}")
            
        except WebDriverException as e:
            error_msg = f"Failed to set window size: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def maximize_window(self) -> None:
        """Maximize the browser window.
        
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            BrowserError: If maximizing window fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug("Maximizing browser window")
            self._driver.maximize_window()
            self._logger.debug("Browser window maximized")
            
        except WebDriverException as e:
            error_msg = f"Failed to maximize window: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def minimize_window(self) -> None:
        """Minimize the browser window.
        
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            BrowserError: If minimizing window fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug("Minimizing browser window")
            self._driver.minimize_window()
            self._logger.debug("Browser window minimized")
            
        except WebDriverException as e:
            error_msg = f"Failed to minimize window: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def fullscreen_window(self) -> None:
        """Make the browser window fullscreen.
        
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            BrowserError: If making window fullscreen fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug("Setting browser window to fullscreen")
            self._driver.fullscreen_window()
            self._logger.debug("Browser window set to fullscreen")
            
        except WebDriverException as e:
            error_msg = f"Failed to set window to fullscreen: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    # Browser Information
    
    def get_browser_type(self) -> str:
        """Get the browser type.
        
        Returns:
            The browser type as a string ("chrome").
        """
        return "chrome"
    
    # Tab Management
    
    def new_tab(self, url: Optional[str] = None, switch: bool = True) -> str:
        """Open a new browser tab.
        
        Args:
            url: Optional URL to load in the new tab.
            switch: Whether to switch to the new tab.
            
        Returns:
            The window handle of the new tab.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            BrowserError: If creating a new tab fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug("Opening new tab")
            self._driver.execute_script("window.open('');")
            
            # Get the new window handle
            new_window = [handle for handle in self._driver.window_handles 
                        if handle != self._driver.current_window_handle][-1]
            
            if switch:
                self.switch_to_tab(new_window)
            
            # Navigate to URL if provided
            if url:
                self.get(url)
            
            self._logger.debug(f"Opened new tab with handle: {new_window}")
            return new_window
            
        except WebDriverException as e:
            error_msg = f"Failed to open new tab: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def close_tab(self, window_handle: Optional[str] = None) -> None:
        """Close the current or specified browser tab.
        
        Args:
            window_handle: Optional window handle of the tab to close. 
                         If None, closes the current tab.
                         
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            BrowserError: If closing the tab fails.
        """
        self._check_browser_initialized()
        
        try:
            if window_handle:
                # Switch to the tab first if it's not the current one
                if window_handle != self._driver.current_window_handle:
                    self.switch_to_tab(window_handle)
            
            self._logger.debug(f"Closing tab with handle: {window_handle or 'current'}")
            self._driver.close()
            self._logger.debug("Tab closed successfully")
            
        except WebDriverException as e:
            error_msg = f"Failed to close tab: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def switch_to_tab(self, window_handle: str) -> None:
        """Switch to a specific browser tab.
        
        Args:
            window_handle: The window handle of the tab to switch to.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            BrowserError: If switching tabs fails.
        """
        self._check_browser_initialized()
        
        try:
            if window_handle not in self._driver.window_handles:
                raise BrowserError(f"No such window handle: {window_handle}")
                
            self._logger.debug(f"Switching to tab with handle: {window_handle}")
            self._driver.switch_to.window(window_handle)
            self._logger.debug("Successfully switched tabs")
            
        except WebDriverException as e:
            error_msg = f"Failed to switch to tab: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def get_current_tab_handle(self) -> str:
        """Get the handle of the current tab.
        
        Returns:
            The window handle of the current tab.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        return self._driver.current_window_handle
    
    def get_tab_handles(self) -> List[str]:
        """Get handles of all open tabs.
        
        Returns:
            A list of window handles for all open tabs.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        return self._driver.window_handles
    
    # Page Information
    
    def get_current_url(self) -> str:
        """Get the current page URL.
        
        Returns:
            The current URL as a string.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        return self._driver.current_url
    
    def get_page_title(self) -> str:
        """Get the current page title.
        
        Returns:
            The page title as a string.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        return self._driver.title
    
    def get_page_source(self) -> str:
        """Get the current page source.
        
        Returns:
            The page source as a string.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        return self._driver.page_source
    
    # Helper Methods
    
    # Cookie Management
    
    def add_cookie(self, name: str, value: str, **kwargs) -> None:
        """Add a cookie to the current page.
        
        Args:
            name: Cookie name.
            value: Cookie value.
            **kwargs: Additional cookie attributes (domain, path, secure, expiry, etc.).
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            BrowserError: If adding the cookie fails.
        """
        self._check_browser_initialized()
        
        try:
            cookie = {'name': name, 'value': value, **kwargs}
            self._logger.debug(f"Adding cookie: {name}={value}")
            self._driver.add_cookie(cookie)
            self._logger.debug("Cookie added successfully")
            
        except WebDriverException as e:
            error_msg = f"Failed to add cookie {name}: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def get_cookie(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a cookie by name.
        
        Args:
            name: Name of the cookie to retrieve.
            
        Returns:
            Cookie dictionary if found, None otherwise.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        return self._driver.get_cookie(name)
    
    def get_all_cookies(self) -> List[Dict[str, Any]]:
        """Get all cookies for the current page.
        
        Returns:
            List of cookie dictionaries.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        return self._driver.get_cookies()
    
    def delete_cookie(self, name: str) -> None:
        """Delete a cookie by name.
        
        Args:
            name: Name of the cookie to delete.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            BrowserError: If deleting the cookie fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug(f"Deleting cookie: {name}")
            self._driver.delete_cookie(name)
            self._logger.debug("Cookie deleted successfully")
            
        except WebDriverException as e:
            error_msg = f"Failed to delete cookie {name}: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def delete_all_cookies(self) -> None:
        """Delete all cookies for the current page.
        
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            BrowserError: If deleting cookies fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug("Deleting all cookies")
            self._driver.delete_all_cookies()
            self._logger.debug("All cookies deleted successfully")
            
        except WebDriverException as e:
            error_msg = f"Failed to delete all cookies: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    # Screenshot Methods
    
    def take_screenshot(self, filepath: Optional[str] = None) -> Union[bytes, str]:
        """Take a screenshot of the current page.
        
        Args:
            filepath: Optional path to save the screenshot. If None, returns the image as bytes.
            
        Returns:
            If filepath is None, returns the screenshot as bytes.
            If filepath is provided, returns the filepath where the screenshot was saved.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            ScreenshotError: If taking the screenshot fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug("Taking screenshot")
            screenshot = self._driver.get_screenshot_as_png()
            
            if filepath:
                try:
                    with open(filepath, 'wb') as f:
                        f.write(screenshot)
                    self._logger.debug(f"Screenshot saved to {filepath}")
                    return filepath
                except IOError as e:
                    error_msg = f"Failed to save screenshot to {filepath}: {e}"
                    self._logger.error(error_msg)
                    raise ScreenshotError(error_msg) from e
            
            self._logger.debug("Screenshot taken successfully")
            return screenshot
            
        except WebDriverException as e:
            error_msg = f"Failed to take screenshot: {e}"
            self._logger.error(error_msg)
            raise ScreenshotError(error_msg) from e
    
    def take_element_screenshot(self, element, filepath: Optional[str] = None) -> Union[bytes, str]:
        """Take a screenshot of a specific element.
        
        Args:
            element: The WebElement to capture.
            filepath: Optional path to save the screenshot. If None, returns the image as bytes.
            
        Returns:
            If filepath is None, returns the screenshot as bytes.
            If filepath is provided, returns the filepath where the screenshot was saved.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            ScreenshotError: If taking the element screenshot fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug("Taking element screenshot")
            screenshot = element.screenshot_as_png
            
            if filepath:
                try:
                    with open(filepath, 'wb') as f:
                        f.write(screenshot)
                    self._logger.debug(f"Element screenshot saved to {filepath}")
                    return filepath
                except IOError as e:
                    error_msg = f"Failed to save element screenshot to {filepath}: {e}"
                    self._logger.error(error_msg)
                    raise ScreenshotError(error_msg)
            
            self._logger.debug("Element screenshot taken successfully")
            return screenshot
            
        except WebDriverException as e:
            error_msg = f"Failed to take element screenshot: {e}"
            self._logger.error(error_msg)
            raise ScreenshotError(error_msg) from e
    
    # Helper Methods
    
    # JavaScript Execution
    
    def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript in the current page context.
        
        Args:
            script: The JavaScript code to execute.
            *args: Arguments to pass to the script.
            
        Returns:
            The result of the script execution.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            BrowserError: If script execution fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug(f"Executing JavaScript: {script[:100]}...")
            result = self._driver.execute_script(script, *args)
            return result
            
        except WebDriverException as e:
            error_msg = f"JavaScript execution failed: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def execute_async_script(self, script: str, *args) -> Any:
        """Execute asynchronous JavaScript in the current page context.
        
        Args:
            script: The JavaScript code to execute.
            *args: Arguments to pass to the script.
            
        Returns:
            The result of the script execution.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            BrowserError: If script execution fails.
        """
        self._check_browser_initialized()
        
        try:
            self._logger.debug(f"Executing async JavaScript: {script[:100]}...")
            result = self._driver.execute_async_script(script, *args)
            return result
            
        except WebDriverException as e:
            error_msg = f"Async JavaScript execution failed: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    # Alert Handling
    
    def accept_alert(self) -> None:
        """Accept the currently displayed alert.
        
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            NoAlertPresentException: If no alert is present.
        """
        self._check_browser_initialized()
        self._driver.switch_to.alert.accept()
    
    def dismiss_alert(self) -> None:
        """Dismiss the currently displayed alert.
        
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            NoAlertPresentException: If no alert is present.
        """
        self._check_browser_initialized()
        self._driver.switch_to.alert.dismiss()
    
    def get_alert_text(self) -> str:
        """Get the text of the currently displayed alert.
        
        Returns:
            The alert text.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            NoAlertPresentException: If no alert is present.
        """
        self._check_browser_initialized()
        return self._driver.switch_to.alert.text
    
    def send_keys_to_alert(self, text: str) -> None:
        """Send keys to the currently displayed alert.
        
        Args:
            text: The text to send to the alert.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            NoAlertPresentException: If no alert is present.
        """
        self._check_browser_initialized()
        self._driver.switch_to.alert.send_keys(text)
    
    # Timeouts
    
    def set_page_load_timeout(self, timeout: float) -> None:
        """Set the amount of time to wait for a page load to complete.
        
        Args:
            timeout: Time to wait in seconds.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        self._driver.set_page_load_timeout(timeout)
    
    def set_script_timeout(self, timeout: float) -> None:
        """Set the amount of time to wait for an asynchronous script to finish.
        
        Args:
            timeout: Time to wait in seconds.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        self._driver.set_script_timeout(timeout)
    
    def set_implicit_wait(self, timeout: float) -> None:
        """Set the amount of time to wait for implicit element location.
        
        Args:
            timeout: Time to wait in seconds.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        self._driver.implicitly_wait(timeout)
    
    # Element Interaction
    
    def find_element(self, by: str, value: str):
        """Find an element on the page.
        
        Args:
            by: The locator strategy to use (e.g., 'id', 'name', 'xpath', etc.).
            value: The value of the locator.
            
        Returns:
            The first WebElement matching the locator.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
            NoSuchElementException: If no element is found.
        """
        self._check_browser_initialized()
        return self._driver.find_element(by, value)
    
    def find_elements(self, by: str, value: str) -> List[Any]:
        """Find all elements on the page matching the locator.
        
        Args:
            by: The locator strategy to use (e.g., 'id', 'name', 'xpath', etc.).
            value: The value of the locator.
            
        Returns:
            A list of WebElements matching the locator (empty if none found).
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        return self._driver.find_elements(by, value)
    
    def wait_for_element(self, by: str, value: str, timeout: float = 10) -> Any:
        """Wait for an element to be present on the page.
        
        Args:
            by: The locator strategy to use.
            value: The value of the locator.
            timeout: Maximum time to wait in seconds.
            
        Returns:
            The WebElement once it is found.
            
        Raises:
            TimeoutException: If the element is not found within the timeout.
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        return WebDriverWait(self._driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    # Browser Information
    
    def get_browser_name(self) -> str:
        """Get the name of the browser.
        
        Returns:
            The browser name (always 'chrome' for this implementation).
        """
        return "chrome"
    
    def get_browser_version(self) -> str:
        """Get the version of the browser.
        
        Returns:
            The browser version string.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        return self._driver.capabilities.get('browserVersion', 'unknown')
    
    def get_platform(self) -> str:
        """Get the platform the browser is running on.
        
        Returns:
            The platform name.
            
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        self._check_browser_initialized()
        return self._driver.capabilities.get('platformName', 'unknown')
    
    # Context Management
    
    def __enter__(self) -> 'ChromeBrowser':
        """Context manager entry point."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit point."""
        self.stop()
    
    # Helper Methods
    
    def _check_browser_initialized(self) -> None:
        """Check if the browser is properly initialized and running.
        
        Raises:
            BrowserNotInitializedError: If the browser is not running.
        """
        if not self._is_running or self._driver is None:
            raise BrowserNotInitializedError("Browser is not running or not properly initialized")
    
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
            if isinstance(self.config.window_size, tuple) and len(self.config.window_size) == 2:
                width, height = self.config.window_size
                options.add_argument(f"--window-size={width},{height}")
            elif hasattr(self.config.window_size, 'width') and hasattr(self.config.window_size, 'height'):
                options.add_argument(f"--window-size={self.config.window_size.width},{self.config.window_size.height}")
        
        # Set user agent if provided
        if self.config.user_agent:
            options.add_argument(f"--user-agent={self.config.user_agent}")
        
        # Add chrome arguments from config
        for arg in self.config.chrome_arguments or []:
            options.add_argument(arg)
            
        # Add any additional chrome options
        for key, value in (self.config.chrome_options or {}).items():
            options.set_capability(key, value)
        
        # Set experimental options
        if self.config.experimental_options:
            for key, value in self.config.experimental_options.items():
                options.set_experimental_option(key, value)
        
        # Set performance settings
        if self.config.disable_gpu:
            options.add_argument("--disable-gpu")
            
        if self.config.no_sandbox:
            options.add_argument("--no-sandbox")
            
        if self.config.disable_dev_shm_usage:
            options.add_argument("--disable-dev-shm-usage")
        
        return options
    
    def _create_service(self) -> ChromeService:
        """Create and configure the Chrome service.
        
        Returns:
            Configured ChromeService instance.
        """
        # Use default log path if not specified
        log_path = self.config.log_file or "chromedriver.log"
        
        # Create service with minimal required arguments
        # Note: Newer versions of Selenium don't require executable_path
        service = ChromeService(
            log_path=log_path
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
