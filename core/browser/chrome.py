"""Chrome browser implementation using Selenium WebDriver."""
import os
import sys
import platform
import shutil
import struct
import zipfile
import urllib.request
import logging
from pathlib import Path
from typing import Optional, Any, Dict, Tuple, Union

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from .base import BaseBrowser
from .exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError,
    ScreenshotError,
    ElementNotFoundError,
    ElementNotInteractableError,
    TimeoutError as BrowserTimeoutError
)


class ChromeBrowser(BaseBrowser):
    """Chrome browser implementation for web automation.
    
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
        self.driver = None
        self._service = None
        self._is_running = False
        self._logger = logger or logging.getLogger(__name__)

    def _get_chrome_version(self) -> Optional[str]:
        """Detect installed Chrome version.
        
        Returns:
            Optional[str]: Chrome version string or None if not found
        """
        try:
            if platform.system() == "Windows":
                import winreg
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Google\Chrome\BLBeacon"
                ) as key:
                    version = winreg.QueryValueEx(key, 'version')[0]
                    return version.split('.')[0]  # Return major version
            else:
                # For macOS and Linux
                import subprocess
                result = subprocess.run(
                    ['google-chrome', '--version'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.strip().split()[-1].split('.')[0]
        except Exception as e:
            self._logger.warning(f"Could not detect Chrome version: {e}")
        return None
        
    def _get_chrome_bitness(self) -> str:
        """Detect Chrome installation bitness.
        
        Returns:
            str: '32' or '64' indicating Chrome bitness
        """
        try:
            if platform.system() == "Windows":
                import winreg
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Google\Chrome\BLBeacon"
                ) as key:
                    install_path = winreg.QueryValueEx(key, 'Path')[0]
                    chrome_exe = os.path.join(install_path, 'chrome.exe')
                    with open(chrome_exe, 'rb') as f:
                        f.seek(0x3C)  # PE header offset
                        pe_offset = struct.unpack('<I', f.read(4))[0]
                        f.seek(pe_offset + 4)  # PE signature + machine type
                        machine_type = struct.unpack('<H', f.read(2))[0]
                        return '64' if machine_type == 0x8664 else '32'
            # For non-Windows, assume 64-bit
            return '64'
        except Exception as e:
            self._logger.warning(f"Could not detect Chrome bitness: {e}")
            return '64'  # Default to 64-bit
            
    def _get_python_bitness(self) -> str:
        """Get Python interpreter bitness.
        
        Returns:
            str: '32' or '64' indicating Python bitness
        """
        return '64' if struct.calcsize("P") * 8 == 64 else '32'
        
    def _download_chromedriver(self, version: str, bitness: str, target_path: Path) -> bool:
        """Download and save ChromeDriver matching the specified version and bitness.
        
        Args:
            version: Chrome major version number as string
            bitness: '32' or '64' indicating required bitness
            target_path: Path where to save the downloaded ChromeDriver
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        try:
            # Construct download URL
            base_url = "https://chromedriver.storage.googleapis.com"
            url = f"{base_url}/{version}.0.0/chromedriver_win{bitness}.zip"
            
            self._logger.info(f"Downloading ChromeDriver {version} ({bitness}-bit) from: {url}")
            
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
            chromedriver_exe = next(temp_dir.glob("**/chromedriver*"), None)
            if not chromedriver_exe or not chromedriver_exe.is_file():
                self._logger.error("ChromeDriver executable not found in downloaded archive")
                return False
                
            # Move to target location
            if target_path.exists():
                target_path.unlink()
            shutil.move(str(chromedriver_exe), str(target_path))
            
            # Set executable permissions on Unix-like systems
            if platform.system() != "Windows":
                target_path.chmod(0o755)
                
            self._logger.info(f"Successfully downloaded ChromeDriver to: {target_path}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to download ChromeDriver: {e}")
            return False
        finally:
            # Clean up temp directory
            if 'temp_dir' in locals() and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                
    def _setup_chrome_options(self) -> ChromeOptions:
        """Set up Chrome options with configured settings.
        
        Returns:
            ChromeOptions: Configured Chrome options
        """
        options = ChromeOptions()
        
        # Set headless mode if specified
        if getattr(self.config, 'headless', False):
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            
        # Add additional Chrome arguments
        for arg in getattr(self.config, 'chrome_arguments', []):
            if arg not in ["--headless", "--disable-gpu"]:  # Avoid duplicates
                options.add_argument(arg)
                
        # Set custom user agent if specified
        if hasattr(self.config, 'user_agent') and self.config.user_agent:
            options.add_argument(f"user-agent={self.config.user_agent}")
        
        # Set window size if specified
        if hasattr(self.config, 'window_size') and self.config.window_size:
            options.add_argument(
                f"--window-size={self.config.window_size[0]},{self.config.window_size[1]}"
            )
        else:
            options.add_argument("--start-maximized")
        
        # Additional performance and stability options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Disable automation flags detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        return options
        
    def _create_driver(self) -> webdriver.Chrome:
        """Create and configure a Chrome WebDriver instance.
        
        Returns:
            webdriver.Chrome: Configured WebDriver instance
            
        Raises:
            BrowserError: If WebDriver initialization fails
        """
        options = self._setup_chrome_options()
        
        # 1. Try using configured chromedriver path first
        if hasattr(self.config, 'chromedriver_path') and self.config.chromedriver_path:
            try:
                self._logger.info(
                    f"Using configured ChromeDriver: {self.config.chromedriver_path}"
                )
                service = Service(executable_path=str(self.config.chromedriver_path))
                return webdriver.Chrome(service=service, options=options)
            except Exception as e:
                self._logger.warning(f"Configured ChromeDriver failed: {e}")
        
        # 2. Try to detect Chrome version and download matching driver
        try:
            chrome_version = self._get_chrome_version()
            chrome_bitness = self._get_chrome_bitness()
            python_bitness = self._get_python_bitness()
            
            self._logger.info(
                f"Detected - Chrome: {chrome_version} ({chrome_bitness}-bit), "
                f"Python: {python_bitness}-bit"
            )
            
            # 3. If architectures match, try to download matching ChromeDriver
            if chrome_version and chrome_bitness == python_bitness:
                driver_path = (
                    Path.home() / ".chromedriver" / 
                    f"chromedriver_{chrome_version}_{chrome_bitness}"
                )
                driver_path.parent.mkdir(parents=True, exist_ok=True)
                
                if not driver_path.exists() and self._download_chromedriver(
                    chrome_version, python_bitness, driver_path
                ):
                    try:
                        service = Service(executable_path=str(driver_path))
                        return webdriver.Chrome(service=service, options=options)
                    except Exception as e:
                        self._logger.warning(f"Downloaded ChromeDriver failed: {e}")
        except Exception as e:
            self._logger.warning(f"Chrome version detection failed: {e}")
        
        # 4. Fall back to webdriver-manager
        try:
            self._logger.info("Falling back to webdriver-manager for ChromeDriver")
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
        except Exception as e:
            self._logger.warning(f"webdriver-manager fallback failed: {e}")
            
        # 5. Final fallback - try system PATH
        try:
            self._logger.info("Attempting to use ChromeDriver from system PATH")
            return webdriver.Chrome(options=options)
        except Exception as e:
            error_msg = (
                "All ChromeDriver initialization methods failed. "
                "Please ensure Chrome and ChromeDriver are properly installed.\n"
                f"Error: {e}"
            )
            self._logger.error(error_msg)
            raise BrowserError(error_msg) from e
            
    def _cleanup_resources(self) -> None:
        """Clean up browser resources."""
        if hasattr(self, 'driver') and self.driver:
            try:
                # Try to close all windows and quit the browser
                if hasattr(self.driver, 'window_handles') and self.driver.window_handles:
                    self.driver.quit()
                    self._logger.debug("Browser quit successfully")
            except Exception as e:
                self._logger.error(f"Error while quitting browser: {e}")
            finally:
                self.driver = None
                self._is_running = False
        
        # Stop the Chrome service if it exists
        if hasattr(self, '_service') and self._service:
            try:
                self._service.stop()
                self._logger.debug("Chrome service stopped")
            except Exception as e:
                self._logger.error(f"Error stopping Chrome service: {e}")
            finally:
                self._service = None
                
    def start(self) -> None:
        """Start the Chrome browser with the configured settings.
        
        Raises:
            BrowserError: If the browser fails to start
        """
        if self._is_running:
            self._logger.warning("Browser is already running")
            return
                
        try:
            # Create and configure the WebDriver
            self._logger.info("Initializing Chrome browser...")
            self.driver = self._create_driver()
            self._is_running = True
                
            # Set default window size if not in headless mode
            if not getattr(self.config, 'headless', False) and \
               hasattr(self.config, 'window_size') and self.config.window_size:
                self.driver.set_window_size(
                    self.config.window_size[0],
                    self.config.window_size[1]
                )
                    
            self._logger.info("Chrome browser started successfully")
            
        except Exception as e:
            error_msg = f"Failed to start Chrome browser: {e}"
            self._logger.error(error_msg)
            self._cleanup_resources()
            raise BrowserError(error_msg) from e
            
    def stop(self) -> None:
        """Stop the browser and clean up resources."""
        if not self._is_running:
            self._logger.warning("Browser is not running")
            return
            
        try:
            self._cleanup_resources()
            self._logger.info("Browser stopped successfully")
        except Exception as e:
            self._logger.error(f"Error while stopping browser: {e}")
            raise BrowserError(f"Failed to stop browser: {e}") from e
            
    def navigate_to(self, url: str, wait_time: Optional[float] = None) -> bool:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            wait_time: Optional time to wait for page load (seconds)
            
        Returns:
            bool: True if navigation was successful
            
        Raises:
            BrowserNotInitializedError: If browser is not started
            NavigationError: If navigation fails
        """
        if not self._is_running or not self.driver:
            raise BrowserNotInitializedError("Browser is not running")
            
        try:
            self.driver.get(url)
            
            # Wait for page load if wait_time is specified
            if wait_time is not None:
                self.driver.implicitly_wait(wait_time)
                
            return True
            
        except Exception as e:
            error_msg = f"Failed to navigate to {url}: {e}"
            self._logger.error(error_msg)
            raise NavigationError(error_msg) from e
            
    def get_page_source(self) -> str:
        """Get the current page source.
        
        Returns:
            str: The page source HTML
            
        Raises:
            BrowserNotInitializedError: If browser is not started
        """
        if not self._is_running or not self.driver:
            raise BrowserNotInitializedError("Browser is not running")
            
        return self.driver.page_source
        
    def get_current_url(self) -> str:
        """Get the current URL.
        
        Returns:
            str: The current URL
            
        Raises:
            BrowserNotInitializedError: If browser is not started
        """
        if not self._is_running or not self.driver:
            raise BrowserNotInitializedError("Browser is not running")
            
        return self.driver.current_url
        
    def take_screenshot(self, file_path: str, full_page: bool = False) -> bool:
        """Take a screenshot of the current page.
        
        Args:
            file_path: Path to save the screenshot
            full_page: If True, capture the full page (requires JavaScript)
            
        Returns:
            bool: True if screenshot was successful
            
        Raises:
            BrowserNotInitializedError: If browser is not started
            ScreenshotError: If screenshot capture fails
        """
        if not self._is_running or not self.driver:
            raise BrowserNotInitializedError("Browser is not running")
            
        try:
            if full_page:
                # Scroll and stitch approach for full page screenshot
                total_height = self.driver.execute_script(
                    "return document.body.scrollHeight"
                )
                viewport_height = self.driver.execute_script(
                    "return window.innerHeight"
                )
                
                # Take multiple screenshots and stitch them
                # (Implementation left as an exercise)
                # For now, fall back to viewport screenshot
                self.driver.save_screenshot(file_path)
            else:
                self.driver.save_screenshot(file_path)
                
            return True
            
        except Exception as e:
            error_msg = f"Failed to take screenshot: {e}"
            self._logger.error(error_msg)
            raise ScreenshotError(error_msg) from e
            
    def is_running(self) -> bool:
        """Check if the browser is running.
        
        Returns:
            bool: True if the browser is running
        """
        return self._is_running and self.driver is not None
        
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False  # Don't suppress exceptions
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  r"Software\Google\Chrome\BLBeacon") as key:
                    version = winreg.QueryValueEx(key, 'version')[0]
                    return version.split('.')[0]  # Return major version
            else:
                # For macOS and Linux
                import subprocess
                result = subprocess.run(['google-chrome', '--version'], 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip().split()[-1].split('.')[0]
        except Exception as e:
            self._logger.warning(f"Could not detect Chrome version: {e}")
        return None

    def _get_chrome_bitness(self) -> str:
        """Detect Chrome installation bitness.
        
        Returns:
            str: '32' or '64' indicating Chrome bitness
        """
        try:
            if platform.system() == "Windows":
                import winreg
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  r"Software\Google\Chrome\BLBeacon") as key:
                    install_path = winreg.QueryValueEx(key, 'Path')[0]
                    chrome_exe = os.path.join(install_path, 'chrome.exe')
                    with open(chrome_exe, 'rb') as f:
                        f.seek(0x3C)  # PE header offset
                        pe_offset = struct.unpack('<I', f.read(4))[0]
                        f.seek(pe_offset + 4)  # PE signature + machine type
                        machine_type = struct.unpack('<H', f.read(2))[0]
                        return '64' if machine_type == 0x8664 else '32'
            else:
                # For non-Windows, assume 64-bit
                return '64'
        except Exception as e:
            self._logger.warning(f"Could not detect Chrome bitness: {e}")
            return '64'  # Default to 64-bit

    def _get_python_bitness(self) -> str:
        """Get Python interpreter bitness.
    
        Returns:
            str: '32' or '64' indicating Python bitness
        """
        return '64' if struct.calcsize("P") * 8 == 64 else '32'

    def _download_chromedriver(self, version: str, bitness: str, target_path: Path) -> bool:
        """Download and save ChromeDriver matching the specified version and bitness.
    
        Args:
            version: Chrome major version number as string
            bitness: '32' or '64' indicating required bitness
            target_path: Path where to save the downloaded ChromeDriver
        
        Returns:
            bool: True if download was successful, False otherwise
        """
        try:
            # Construct download URL
            base_url = "https://chromedriver.storage.googleapis.com"
            url = f"{base_url}/{version}.0.0/chromedriver_win{bitness}.zip"
        
            self._logger.info(f"Downloading ChromeDriver {version} ({bitness}-bit) from: {url}")
        
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
            chromedriver_exe = next(temp_dir.glob("**/chromedriver*"), None)
            if not chromedriver_exe or not chromedriver_exe.is_file():
                self._logger.error("ChromeDriver executable not found in downloaded archive")
                return False
            
        # Move to target location
        if target_path.exists():
            target_path.unlink()
        shutil.move(str(chromedriver_exe), str(target_path))
        
        # Set executable permissions on Unix-like systems
        if platform.system() != "Windows":
            target_path.chmod(0o755)
            
            self._logger.info(f"Successfully downloaded ChromeDriver to: {target_path}")
            return True
        
        except Exception as e:
            self._logger.error(f"Failed to download ChromeDriver: {e}")
            return False
        finally:
            # Clean up temp directory
            if 'temp_dir' in locals() and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

# Fix the _setup_chrome_options method
    def _setup_chrome_options(self) -> ChromeOptions:
    """Set up Chrome options with configured settings.
    
    Returns:
        ChromeOptions: Configured Chrome options
    """
    options = ChromeOptions()
    
    # Set headless mode if specified
    if self.config.headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        
    # Add additional Chrome arguments
    for arg in self.config.chrome_arguments:
        if arg not in ["--headless", "--disable-gpu"]:  # Avoid duplicates
            options.add_argument(arg)
            
    # Set custom user agent if specified
    if self.config.user_agent:
        options.add_argument(f"user-agent={self.config.user_agent}")
    
    # Set window size
    if self.config.window_size:
        options.add_argument(f"--window-size={self.config.window_size[0]},{self.config.window_size[1]}")
    else:
        options.add_argument("--start-maximized")
    
    # Additional performance and stability options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Disable automation flags detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    return options

# Add the missing _cleanup_resources method
    def _cleanup_resources(self) -> None:
    """Clean up browser resources."""
    if hasattr(self, 'driver') and self.driver:
        try:
            # Try to close all windows and quit the browser
            if self.driver.window_handles:
                self.driver.quit()
                self._logger.debug("Browser quit successfully")
        except Exception as e:
            self._logger.error(f"Error while quitting browser: {e}")
        finally:
            self.driver = None
            self._is_running = False
    
    # Stop the Chrome service if it exists
    if hasattr(self, '_service') and self._service:
        try:
            self._service.stop()
            self._logger.debug("Chrome service stopped")
        except Exception as e:
            self._logger.error(f"Error stopping Chrome service: {e}")
        finally:
            self._service = None

    def _create_driver(self) -> webdriver.Chrome:
    """Create and configure a Chrome WebDriver instance with automatic driver management.
    
    This method implements a multi-layered approach to WebDriver initialization:
    1. First tries to use the configured chromedriver path
    2. Falls back to webdriver-manager if available
    3. Attempts to automatically download a matching ChromeDriver
        
    Returns:
        webdriver.Chrome: Configured WebDriver instance
            
    Raises:
        BrowserError: If all driver initialization methods fail
    """
    options = self._setup_chrome_options()
    
    # 1. Try using configured chromedriver path first
    if self.config.chromedriver_path and self.config.chromedriver_path.exists():
        try:
            self._logger.info(f"Using configured ChromeDriver: {self.config.chromedriver_path}")
            service = Service(executable_path=str(self.config.chromedriver_path))
            return webdriver.Chrome(service=service, options=options)
        except Exception as e:
            self._logger.warning(f"Configured ChromeDriver failed: {e}")
        
    # 2. Detect Chrome version and bitness
    chrome_version = self._get_chrome_version()
    chrome_bitness = self._get_chrome_bitness()
    python_bitness = self._get_python_bitness()
    
    self._logger.info(f"Detected - Chrome: {chrome_version} ({chrome_bitness}-bit), "
                     f"Python: {python_bitness}-bit")
    
    # 3. If bitness matches, try to download matching ChromeDriver
    if chrome_version and chrome_bitness == python_bitness:
        driver_path = Path.home() / ".chromedriver" / f"chromedriver_{chrome_version}_{chrome_bitness}"
        driver_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not driver_path.exists() and self._download_chromedriver(chrome_version, python_bitness, driver_path):
            try:
                service = Service(executable_path=str(driver_path))
                return webdriver.Chrome(service=service, options=options)
            except Exception as e:
                self._logger.warning(f"Downloaded ChromeDriver failed: {e}")
        
    # 4. Fall back to webdriver-manager
    try:
        self._logger.info("Falling back to webdriver-manager for ChromeDriver")
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    except Exception as e:
        self._logger.warning(f"webdriver-manager fallback failed: {e}")
            
    # 5. Final fallback - try system PATH
    try:
        self._logger.info("Attempting to use ChromeDriver from system PATH")
        return webdriver.Chrome(options=options)
    except Exception as e:
        error_msg = (f"All ChromeDriver initialization methods failed. "
                   f"Please ensure Chrome and ChromeDriver are properly installed.\n"
                   f"Error: {e}")
        self._logger.error(error_msg)
        raise BrowserError(error_msg) from e

    def start(self) -> None:
    """
    Start the Chrome browser with the configured settings.
    
    Raises:
        BrowserError: If the browser fails to start
    """
    if self._is_running:
        self._logger.warning("Browser is already running")
        return
            
    try:
        # Create and configure the WebDriver
        self._logger.info("Initializing Chrome browser...")
        self._driver = self._create_driver()
        self._is_running = True
            
        # Set default window size if not in headless mode
        if not self.config.headless and self.config.window_size:
            self._driver.set_window_size(
                self.config.window_size[0],
                self.config.window_size[1]
            )
                
        self._logger.info("Chrome browser started successfully")
            
    except Exception as e:
        error_msg = f"Failed to start Chrome browser: {e}"

    def stop(self) -> None:
        """Stop the browser and clean up resources."""
        if not self._is_running or not self.driver:
            self._logger.warning("Browser is not running")
            return

        try:
            self._cleanup_resources()
            self._logger.info("Browser stopped successfully")
        except Exception as e:
            self._logger.error(f"Error while stopping browser: {e}")
            raise BrowserError(f"Failed to stop browser: {e}") from e
        finally:
            self._is_running = False
            self.driver = None
            self._service = None

    def navigate_to(self, url: str, wait_time: Optional[float] = None) -> bool:
        """
        Navigate to the specified URL.

        Args:
            url: The URL to navigate to
            wait_time: Optional time to wait for page load (seconds)
            
        Returns:
            bool: True if navigation was successful
            
        Raises:
            BrowserNotInitializedError: If browser is not started
            NavigationError: If navigation fails
        """
        if not self._is_running or not self.driver:
            raise BrowserNotInitializedError("Browser is not running")
            
        try:
            self.driver.get(url)
            
            # Wait for page load if wait_time is specified
            if wait_time is not None:
                self.driver.implicitly_wait(wait_time)
                
            return True
            
        except Exception as e:
            error_msg = f"Failed to navigate to {url}: {e}"
            self._logger.error(error_msg)
            raise NavigationError(error_msg) from e
            
    def get_page_source(self) -> str:
        """
        Get the current page source.
        
        Returns:
            str: The page source HTML
            
        Raises:
            BrowserNotInitializedError: If browser is not started
        """
        if not self._is_running or not self.driver:
            raise BrowserNotInitializedError("Browser is not running")
            
        return self.driver.page_source
        
    def get_current_url(self) -> str:
        """
        Get the current URL.
        
        Returns:
            str: The current URL
            
        Raises:
            BrowserNotInitializedError: If browser is not started
        """
        if not self._is_running or not self.driver:
            raise BrowserNotInitializedError("Browser is not running")
            
        return self.driver.current_url
        
    def take_screenshot(self, file_path: str, full_page: bool = False) -> bool:
        """
        Take a screenshot of the current page.
        
        Args:
            file_path: Path to save the screenshot
            full_page: If True, capture the full page (requires JavaScript)
            
        Returns:
            bool: True if screenshot was successful
            
        Raises:
            BrowserNotInitializedError: If browser is not started
            ScreenshotError: If screenshot capture fails
        """
        if not self._is_running or not self.driver:
            raise BrowserNotInitializedError("Browser is not running")
            
        try:
            if full_page:
                # Scroll and stitch approach for full page screenshot
                total_height = self.driver.execute_script("return document.body.scrollHeight")
                viewport_height = self.driver.execute_script("return window.innerHeight")
                
                # Take multiple screenshots and stitch them
                # (Implementation left as an exercise)
                # For now, fall back to viewport screenshot
                self.driver.save_screenshot(file_path)
            else:
                self.driver.save_screenshot(file_path)
                
            return True
            
        except Exception as e:
            error_msg = f"Failed to take screenshot: {e}"
            self._logger.error(error_msg)
            raise ScreenshotError(error_msg) from e
            
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False  # Don't suppress exceptions
    """Stop the Chrome browser and clean up resources."""
    if not self._is_running or not self.driver:
        self._logger.warning("Browser is not running")
        return
        
    self._logger.info("Stopping Chrome browser...")
    self._cleanup_resources()
    self._logger.info("Browser stopped successfully")