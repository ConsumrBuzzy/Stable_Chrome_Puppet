"""Chrome browser driver implementation."""
import logging
import os
import platform
import shutil
import struct
import sys
import zipfile
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Type, TypeVar, Callable

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager, ChromeType

from ..base import BaseBrowser
from ..driver_config import DriverConfig
from ..exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError,
    ScreenshotError,
    ElementNotFoundError,
    ElementNotInteractableError,
    TimeoutError as BrowserTimeoutError
)
from ..features.element import ElementHelper
from ..features.navigation import NavigationMixin
from ..features.screenshot import ScreenshotHelper
from . import register_driver, BaseBrowserDriver

# Type variable for generic typing
T = TypeVar('T')

# Type alias for WebDriver
WebDriver = ChromeWebDriver


@register_driver("chrome")
class ChromeDriver(BaseBrowserDriver, NavigationMixin, ElementHelper, ScreenshotHelper):
    """Chrome browser driver implementation.
    
    This class provides a high-level interface for browser automation with Chrome,
    including navigation, element interaction, and screenshot capabilities.
    """
    
    def __init__(self, config: Any, logger: Optional[logging.Logger] = None):
        """Initialize the Chrome browser.
        
        Args:
            config: Configuration object containing browser settings
            logger: Optional logger instance for logging
        """
        super().__init__(config, logger)
        self.driver: Optional[WebDriver] = None
        self._service: Optional[ChromeService] = None
        self._options: Optional[ChromeOptions] = None
        self._setup_options()
    
    @classmethod
    def get_name(cls) -> str:
        """Get the name of the browser driver.
        
        Returns:
            str: The name of the browser ("chrome")
        """
        return "chrome"
    
    def _setup_options(self) -> None:
        """Set up Chrome options based on configuration."""
        self._options = ChromeOptions()
        
        # Get Chrome arguments from config or use defaults
        chrome_args = getattr(self.config, 'chrome_args', [])
        
        # Base Chrome arguments that are always used
        common_args = [
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-blink-features=AutomationControlled',
            '--password-store=basic',  # Use basic password store to prevent keychain prompts
            '--disable-notifications',
            '--disable-infobars',
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--allow-running-insecure-content',
            '--disable-client-side-phishing-detection',
            '--disable-component-update',
            '--disable-default-apps',
            '--disable-hang-monitor',
            '--disable-popup-blocking',
            '--disable-sync',
            '--metrics-recording-only',
            '--no-zygote',
            '--safebrowsing-disable-auto-update',
            '--use-mock-keychain',
            '--remote-debugging-port=0',
            f'--window-size={self.config.window_size[0]},{self.config.window_size[1]}',
        ]
        
        # Add instance isolation flags if preventing interference
        if getattr(self.config, 'prevent_instance_interference', True):
            isolation_args = [
                '--no-startup-window',
                '--disable-background-networking',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-breakpad',
                '--disable-component-extensions-with-background-pages',
                '--disable-ipc-flooding-protection',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
            common_args.extend(isolation_args)
        
        # Add all arguments to options
        existing_args = [arg.split('=')[0] for arg in self._options.arguments]
        for arg in common_args + chrome_args:
            arg_name = arg.split('=')[0]
            if arg_name not in existing_args:
                self._options.add_argument(arg)
                existing_args.append(arg_name)
        
        # Handle user data directory and profile
        if getattr(self.config, 'use_existing_profile', False) and getattr(self.config, 'user_data_dir', None):
            user_data_dir = str(Path(self.config.user_data_dir).absolute())
            profile_dir = self.config.profile_directory or 'Default'
            
            self._logger.info(f"Using existing Chrome profile: {user_data_dir}/{profile_dir}")
            
            # Add profile-related arguments
            profile_args = [
                f'--user-data-dir={user_data_dir}',
                f'--profile-directory={profile_dir}'
            ]
            
            # Add to chrome_args if not already present
            for arg in profile_args:
                if not any(a.startswith(arg.split('=')[0] + '=') for a in chrome_args):
                    chrome_args.append(arg)
                    
            # Add profile directory to experimental options if not set
            if 'prefs' not in getattr(self.config, 'experimental_options', {}):
                self.config.experimental_options['prefs'] = {}
                
            # Ensure profile settings are properly configured
            profile_prefs = {
                'profile.default_content_settings.popups': 1,
                'profile.default_content_setting_values.notifications': 1,
                'credentials_enable_service': True,
                'profile.password_manager_enabled': True
            }
            
            self.config.experimental_options['prefs'].update(profile_prefs)
        
        # Enable password manager if configured
        if getattr(self.config, 'enable_password_manager', True):
            default_args.extend([
                '--enable-automation',
                '--disable-blink-features=AutomationControlled',
            ])
            
            # Add password manager settings to experimental options
            if 'prefs' not in getattr(self.config, 'experimental_options', {}):
                self.config.experimental_options['prefs'] = {}
                
            password_prefs = {
                'credentials_enable_service': True,
                'profile.password_manager_enabled': True,
                'profile.default_content_setting_values.notifications': 1,
                'profile.default_content_settings.popups': 1,
            }
            
            self.config.experimental_options['prefs'].update(password_prefs)
            
            # Enable password manager prompts if configured
            if getattr(self.config, 'enable_password_manager_prompts', True):
                default_args.extend([
                    '--enable-autofill-password-reveal',
                    '--enable-password-manager-reauthentication',
                ])
        else:
            default_args.append('--disable-blink-features=AutomationControlled')
        
        # Add all arguments to options
        for arg in default_args + chrome_args:
            if arg.split('=')[0] not in [a.split('=')[0] for a in self._options.arguments]:
                self._options.add_argument(arg)
        
        # Add experimental options if provided
        experimental_options = getattr(self.config, 'experimental_options', {})
        for key, value in experimental_options.items():
            self._options.add_experimental_option(key, value)
        
        # Set window size if specified
        if hasattr(self.config, 'window_size') and self.config.window_size:
            width, height = self.config.window_size
            self._options.add_argument(f'--window-size={width},{height}')
        
        # Disable automation flags that might trigger bot detection
        self._options.add_experimental_option('excludeSwitches', [
            'enable-automation',
            'enable-logging',
            'load-extension',
            'test-type',
            'ignore-certificate-errors',
            'safebrowsing-disable-auto-update'
        ])
        
        # Additional settings to make automation less detectable
        self._options.add_experimental_option('useAutomationExtension', False)
        self._options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.default_content_setting_values.notifications': 2,  # Disable notifications
            'profile.managed_default_content_settings.images': 1,
            'profile.managed_default_content_settings.javascript': 1,
            'profile.managed_default_content_settings.plugins': 1,
            'profile.managed_default_content_settings.popups': 2,
            'profile.managed_default_content_settings.geolocation': 2,
            'profile.managed_default_content_settings.media_stream': 2,
        })
    
    def navigate_to(self, url: str, wait_time: Optional[float] = None) -> bool:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            wait_time: Optional time to wait for page load
            
        Returns:
            bool: True if navigation was successful
        """
        if not self.driver:
            raise BrowserNotInitializedError("Browser is not initialized. Call start() first.")
        
        try:
            self.driver.get(url)
            if wait_time:
                time.sleep(wait_time)
            return True
        except Exception as e:
            self._logger.error(f"Failed to navigate to {url}: {e}")
            raise NavigationError(f"Failed to navigate to {url}: {e}") from e
    
    def get_page_source(self) -> str:
        """Get the current page source.
        
        Returns:
            str: The page source HTML
        """
        if not self.driver:
            raise BrowserNotInitializedError("Browser is not initialized. Call start() first.")
        return self.driver.page_source
    
    def get_current_url(self) -> str:
        """Get the current URL.
        
        Returns:
            str: The current URL
        """
        if not self.driver:
            raise BrowserNotInitializedError("Browser is not initialized. Call start() first.")
        return self.driver.current_url
    
    def take_screenshot(self, file_path: str, full_page: bool = False) -> bool:
        """Take a screenshot of the current page.
        
        Args:
            file_path: Path to save the screenshot
            full_page: If True, capture the full page (not supported in all browsers)
            
        Returns:
            bool: True if screenshot was successful
        """
        if not self.driver:
            raise BrowserNotInitializedError("Browser is not initialized. Call start() first.")
        
        try:
            self.driver.save_screenshot(file_path)
            return True
        except Exception as e:
            self._logger.error(f"Failed to take screenshot: {e}")
            raise ScreenshotError(f"Failed to take screenshot: {e}") from e
    
    def _create_service(self) -> ChromeService:
        """Create and configure the Chrome service.
        
        Returns:
            ChromeService: Configured Chrome service instance
        """
        driver_config = getattr(self.config, 'driver_config', {})
        
        # Set up service arguments
        service_args = getattr(driver_config, 'service_args', [])
        log_path = getattr(driver_config, 'service_log_path', None)
        
        # Get the driver path, use ChromeDriverManager if not provided
        driver_path = None
        if hasattr(driver_config, 'driver_path') and driver_config.driver_path:
            driver_path = driver_config.driver_path
        else:
            # Use ChromeDriverManager to handle driver installation
            driver_path = ChromeDriverManager().install()
        
        # Create service with configured options
        service = ChromeService(
            executable_path=driver_path,
            service_args=service_args,
            log_path=log_path
        )
        
        return service
    
    def start(self) -> None:
        """Start the Chrome browser."""
        if self.driver is not None:
            self.logger.warning("Browser is already running")
            return
        
        try:
            # Set up Chrome service and options
            self._service = self._create_service()
            
            # Initialize Chrome WebDriver
            self.driver = webdriver.Chrome(
                service=self._service,
                options=self._options
            )
            
            # Configure timeouts
            if hasattr(self.config, 'implicit_wait'):
                self.driver.implicitly_wait(self.config.implicit_wait)
                
            if hasattr(self.config, 'page_load_timeout'):
                self.driver.set_page_load_timeout(self.config.page_load_timeout)
                
            if hasattr(self.config, 'script_timeout'):
                self.driver.set_script_timeout(self.config.script_timeout)
                
            self.logger.info("Chrome browser started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Chrome browser: {e}")
            self._cleanup_resources()
            raise BrowserError(f"Failed to start Chrome browser: {e}") from e
            
    def _cleanup_resources(self) -> None:
        """Clean up any resources used by the browser."""
        try:
            if self._service:
                self._service.stop()
                self._service = None
        except Exception as e:
            self.logger.warning(f"Error cleaning up Chrome service: {e}")
    
    def stop(self) -> None:
        """Stop the Chrome browser and clean up resources."""
        if self.driver is None:
            return
            
        try:
            self.logger.info("Stopping Chrome browser...")
            self.driver.quit()
            self.logger.info("Chrome browser stopped")
        except Exception as e:
            self.logger.error(f"Error stopping Chrome browser: {e}")
            raise
        finally:
            self.driver = None
            self._cleanup_resources()
    
    def is_running(self) -> bool:
        """Check if the browser is running.
        
        Returns:
            bool: True if the browser is running, False otherwise
        """
        try:
            # Try to get the current URL to check if the browser is still responsive
            if self.driver is None:
                return False
                
            # Check if the browser is still responsive
            _ = self.driver.current_url
            return True
            
        except Exception as e:
            self._logger.debug(f"Browser is not running: {e}")
            return False
            
    def start(self) -> None:
        """Start the Chrome browser."""
        if self.driver is not None:
            self._logger.warning("Browser is already running")
            return
        
        try:
            # Set up Chrome service and options
            self._service = self._create_service()
            
            # Initialize Chrome WebDriver
            self.driver = webdriver.Chrome(
                service=self._service,
                options=self._options
            )
            
            # Configure timeouts
            if hasattr(self.config, 'implicit_wait'):
                self.driver.implicitly_wait(self.config.implicit_wait)
                
            if hasattr(self.config, 'page_load_timeout'):
                self.driver.set_page_load_timeout(self.config.page_load_timeout)
                
            if hasattr(self.config, 'script_timeout'):
                self.driver.set_script_timeout(self.config.script_timeout)
                
            self._logger.info("Chrome browser started successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to start Chrome browser: {e}")
            self._cleanup_resources()
            raise BrowserError(f"Failed to start Chrome browser: {e}") from e
            
    def stop(self) -> None:
        """Stop the Chrome browser and clean up resources."""
        if self.driver is None:
            self._logger.warning("Browser is not running")
            return
            
        try:
            self._logger.info("Stopping Chrome browser...")
            self.driver.quit()
            self._logger.info("Chrome browser stopped")
        except Exception as e:
            self._logger.error(f"Error stopping Chrome browser: {e}")
            raise
        finally:
            self.driver = None
            self._cleanup_resources()
            
    def _cleanup_resources(self) -> None:
        """Clean up any resources used by the browser."""
        if self._service is not None:
            try:
                self._service.stop()
            except Exception as e:
                self._logger.error(f"Error stopping Chrome service: {e}")
            finally:
                self._service = None
            
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def __getattr__(self, name):
        """Delegate attribute access to the underlying driver."""
        if self.driver is None:
            raise BrowserNotInitializedError(
                "Browser driver not initialized. Call start() first."
            )
        return getattr(self.driver, name)
    
    @property
    def current_url(self) -> str:
        """Get the current URL."""
        if self.driver is None:
            raise BrowserNotInitializedError("Browser is not running")
        return self.driver.current_url
    
    @property
    def title(self) -> str:
        """Get the current page title."""
        if self.driver is None:
            raise BrowserNotInitializedError("Browser is not running")
        return self.driver.title
    
    def execute_script(self, script: str, *args) -> Any:
        """Execute JavaScript in the current browser context."""
        if self.driver is None:
            raise BrowserNotInitializedError("Browser is not running")
        return self.driver.execute_script(script, *args)
    
    def get(self, url: str) -> None:
        """Navigate to the specified URL."""
        if self.driver is None:
            raise BrowserNotInitializedError("Browser is not running")
        try:
            self.driver.get(url)
            self.logger.debug(f"Navigated to: {url}")
        except TimeoutException as e:
            error_msg = f"Timeout while navigating to {url}"
            self.logger.error(error_msg)
            raise BrowserTimeoutError(error_msg) from e
        except WebDriverException as e:
            error_msg = f"Failed to navigate to {url}: {str(e)}"
            self.logger.error(error_msg)
            raise NavigationError(error_msg) from e
