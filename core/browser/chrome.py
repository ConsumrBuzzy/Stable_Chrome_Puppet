"""
Chrome browser implementation for Chrome Puppet.

This module provides a robust implementation of the BaseBrowser interface
for Chrome, with support for both headed and headless modes, automatic
driver management, and comprehensive error handling.
"""
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Tuple, Callable, TypeVar

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

# Local imports
from .base import BaseBrowser, retry_on_failure
from .exceptions import BrowserError
from ..config import ChromeConfig
from ..utils.logger import get_logger

# Type variable for generic web elements
WebElementT = TypeVar('WebElementT', bound=WebElement)

class ChromeBrowser(BaseBrowser):
    """
    Enhanced Chrome browser implementation with improved version management
    and architecture detection.
    
    This class provides a robust interface for Chrome automation with
    automatic driver management and comprehensive error handling.
    """
    
    def __init__(self, config: ChromeConfig, logger=None):
        """Initialize the Chrome browser with the given configuration.
        
        Args:
            config: Chrome configuration object containing browser settings
            logger: Optional logger instance for logging browser operations
            
        Raises:
            BrowserError: If there's an issue initializing the browser
        """
        super().__init__(config, logger or get_logger(__name__))
        self.config = config
        self.driver: Optional[WebDriver] = None
        self._service = None
        self._is_running = False
        self._chrome_version = None
        self._chrome_architecture = None
    
    def _detect_chrome_version(self) -> str:
        """Detect installed Chrome version.
        
        Returns:
            str: Chrome version string (e.g., "112.0.5615.49")
            
        Raises:
            BrowserError: If Chrome version cannot be detected
        """
        try:
            if platform.system() == "Windows":
                # Try registry first
                try:
                    import winreg
                    reg_path = r"SOFTWARE\Google\Chrome\BLBeacon"
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                        version = winreg.QueryValueEx(key, "version")[0]
                        self._logger.info(f"Detected Chrome version from registry: {version}")
                        return version
                except Exception:
                    pass

                # Fallback to command line
                chrome_paths = [
                    r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                ]
                
                for path in chrome_paths:
                    if os.path.exists(path):
                        output = subprocess.check_output([path, "--version"]).decode()
                        version_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output)
                        if version_match:
                            version = version_match.group(1)
                            self._logger.info(f"Detected Chrome version from binary: {version}")
                            return version
            else:
                # Linux/Mac
                output = subprocess.check_output(["google-chrome", "--version"]).decode()
                version_match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output)
                if version_match:
                    version = version_match.group(1)
                    self._logger.info(f"Detected Chrome version: {version}")
                    return version

            raise BrowserError("Could not detect Chrome version")

        except Exception as e:
            self._logger.error(f"Error detecting Chrome version: {e}")
            raise BrowserError(f"Failed to detect Chrome version: {e}") from e

    def _detect_chrome_architecture(self) -> str:
        """Detect Chrome architecture (32-bit or 64-bit).
        
        Returns:
            str: '32' or '64' indicating the architecture
            
        Raises:
            BrowserError: If architecture cannot be determined
        """
        try:
            if platform.system() == "Windows":
                chrome_paths = [
                    r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                ]
                
                for path in chrome_paths:
                    if os.path.exists(path):
                        # Check if path contains "Program Files (x86)" for 32-bit
                        if "Program Files (x86)" in path:
                            self._chrome_architecture = '32'
                        else:
                            # Default to 64-bit for Program Files
                            self._chrome_architecture = '64'
                        
                        self._logger.info(f"Detected Chrome architecture: {self._chrome_architecture}-bit")
                        return self._chrome_architecture
            
            # Default to 64-bit for non-Windows or if detection fails
            self._chrome_architecture = '64'
            return self._chrome_architecture
            
        except Exception as e:
            self._logger.error(f"Error detecting Chrome architecture: {e}")
            # Default to 64-bit if detection fails
            return '64'
    
    def _get_chrome_driver_path(self) -> str:
        """
        Get the path to the ChromeDriver executable.
        
        Returns:
            str: Path to the ChromeDriver executable
            
        Raises:
            BrowserError: If ChromeDriver cannot be found or installed
        """
        try:
            # Detect Chrome version and architecture
            chrome_version = self._detect_chrome_version()
            chrome_arch = self._detect_chrome_architecture()
            
            # Determine ChromeDriver URL based on version and architecture
            base_version = chrome_version.split('.')[0]
            driver_url = f"https://chromedriver.storage.googleapis.com/{base_version}.0.0/chromedriver_win{chrome_arch}.zip"
            
            # Set up paths
            script_dir = Path(__file__).parent.parent.parent
            driver_dir = script_dir / "bin" / "drivers"
            driver_dir.mkdir(parents=True, exist_ok=True)
            
            driver_path = driver_dir / "chromedriver.exe"
            
            # Download ChromeDriver if it doesn't exist or is incompatible
            if not driver_path.exists() or not self._is_chromedriver_compatible(driver_path, chrome_version):
                self._download_chromedriver(driver_url, driver_path)
            
            self._logger.info(f"Using ChromeDriver from: {driver_path}")
            return str(driver_path)
            
        except Exception as e:
            error_msg = f"Failed to set up ChromeDriver: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
    def _is_chromedriver_compatible(self, driver_path: Path, chrome_version: str) -> bool:
        """Check if ChromeDriver is compatible with the installed Chrome version."""
        if not driver_path.exists():
            return False
            
        try:
            result = subprocess.run(
                [str(driver_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return False
                
            version_match = re.search(r"ChromeDriver\s+([\d.]+)", result.stdout)
            if not version_match:
                return False
                
            driver_version = version_match.group(1)
            return driver_version.split('.')[0] == chrome_version.split('.')[0]
            
        except Exception:
            return False
    
    def _download_chromedriver(self, url: str, target_path: Path) -> None:
        """Download and extract ChromeDriver."""
        try:
            self._logger.info(f"Downloading ChromeDriver from: {url}")
            
            # Create temp directory
            temp_dir = target_path.parent / "temp_chromedriver"
            temp_dir.mkdir(exist_ok=True)
            zip_path = temp_dir / "chromedriver.zip"
            
            # Download the file
            urllib.request.urlretrieve(url, zip_path)
            
            # Extract the file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            # Find the chromedriver executable
            chromedriver_exe = None
            for file in temp_dir.glob("**/chromedriver*"):
                if file.is_file() and not file.name.endswith('.zip'):
                    chromedriver_exe = file
                    break
                    
            if not chromedriver_exe:
                raise BrowserError("Could not find chromedriver executable in downloaded archive")
                
            # Move to target location
            if target_path.exists():
                target_path.unlink()
            shutil.move(str(chromedriver_exe), str(target_path))
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            # Set executable permissions
            if platform.system() != "Windows":
                target_path.chmod(0o755)
                
        
        # Default to 64-bit for non-Windows or if detection fails
        self._chrome_architecture = '64'
        return self._chrome_architecture
        
    except Exception as e:
        self._logger.error(f"Error detecting Chrome architecture: {e}")
        # Default to 64-bit if detection fails
        return '64'
    
def _get_chrome_driver_path(self) -> str:
    """
    Get the path to the ChromeDriver executable.
    
    Returns:
        str: Path to the ChromeDriver executable
        """
        Stop the Chrome browser and clean up resources.
        
        This method ensures all browser processes are properly terminated
        and resources are released.
        """
        if not self._is_running or self.driver is None:
            self._logger.warning("Browser is not running")
            return
            
        self._logger.info("Stopping Chrome browser...")
        
        try:
            # Try to close all windows and quit the browser
            if self.driver.window_handles:
                self.driver.quit()
                self._logger.debug("Browser quit successfully")
        except Exception as e:
            self._logger.error(f"Error while quitting browser: {e}")
            try:
                # Force kill if normal quit fails
                if platform.system() == 'Windows':
                    os.system('taskkill /f /im chromedriver.exe')
                    os.system('taskkill /f /im chrome.exe')
                else:
                    os.system('pkill -f chromedriver')
                    os.system('pkill -f chrome')
                self._logger.warning("Force-killed browser processes")
            except Exception as kill_error:
                self._logger.error(f"Failed to kill browser processes: {kill_error}")
        finally:
            self.driver = None
            self._is_running = False
            
        # Stop the Chrome service if it exists
        if self._service is not None:
            try:
                self._service.stop()
                self._logger.debug("Chrome service stopped")
            except Exception as e:
                self._logger.error(f"Error stopping Chrome service: {e}")
            finally:
                self._service = None
                
        self._logger.info("Browser stopped successfully")
    
    @retry_on_failure(max_retries=2, exceptions=(WebDriverException,))
    def navigate_to(self, url: str, timeout: int = 30) -> None:
        """
        Navigate to the specified URL and wait for the page to load.
        
        Args:
            url: The URL to navigate to
            timeout: Maximum time to wait for page load in seconds
            
        Raises:
            BrowserError: If browser is not initialized
            NavigationError: If navigation fails or times out
        """
        if not self.driver:
            raise BrowserNotInitializedError("Browser is not initialized")
            
        try:
            self._logger.info(f"Navigating to: {url}")
            
            # Set page load timeout
            self.driver.set_page_load_timeout(timeout)
            
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for document.readyState to be complete
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            self._logger.info(f"Successfully navigated to: {self.driver.current_url}")
            
        except TimeoutException as e:
            error_msg = f"Page load timed out after {timeout} seconds: {url}"
            self._logger.error(error_msg)
            raise NavigationError(error_msg) from e
            
        except WebDriverException as e:
            error_msg = f"Navigation failed: {e.msg if hasattr(e, 'msg') else str(e)}"
            self._logger.error(f"{error_msg} - URL: {url}")
            raise NavigationError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error during navigation to {url}: {str(e)}"
            self._logger.error(error_msg, exc_info=True)
            raise NavigationError(error_msg) from e
    
    def get_current_url(self) -> str:
        """
        Get the current URL of the active tab.
        
        Returns:
            str: The current URL
            
        Raises:
            BrowserError: If browser is not initialized or no window is open
        """
        if not self.driver:
            raise BrowserNotInitializedError("Browser is not initialized")
            
        try:
            if not self.driver.window_handles:
                raise BrowserError("No browser windows are open")
                
            return self.driver.current_url
            
        except Exception as e:
            error_msg = f"Failed to get current URL: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
            
    def get_page_source(self) -> str:
        """
        Get the current page source.
        
        Returns:
            str: The page source HTML
            
        Raises:
            BrowserError: If browser is not initialized or no window is open
        """
        if not self.driver:
            raise BrowserNotInitializedError("Browser is not initialized")
            
        try:
            if not self.driver.window_handles:
                raise BrowserError("No browser windows are open")
                
            return self.driver.page_source
            
        except Exception as e:
            error_msg = f"Failed to get page source: {e}"
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
    
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
