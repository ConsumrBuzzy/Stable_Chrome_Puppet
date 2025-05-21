# Add missing imports at the top of the file
from selenium.common.exceptions import TimeoutException
from .exceptions import BrowserNotInitializedError, NavigationError

# Fix the _download_chromedriver method
def _download_chromedriver(self, url: str, target_path: Path) -> None:
    """Download and extract ChromeDriver.
    
    Args:
        url: URL to download ChromeDriver from
        target_path: Path where ChromeDriver should be saved
        
    Raises:
        BrowserError: If download or extraction fails
    """
    temp_dir = target_path.parent / "temp_chromedriver"
    try:
        self._logger.info(f"Downloading ChromeDriver from: {url}")
        
        # Create temp directory
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
        
        # Set executable permissions
        if platform.system() != "Windows":
            target_path.chmod(0o755)
            
    except Exception as e:
        error_msg = f"Failed to download ChromeDriver: {e}"
        self._logger.error(error_msg)
        raise BrowserError(error_msg) from e
    finally:
        # Clean up temp directory
        if temp_dir.exists():
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

# Add the start method
@retry_on_failure(max_retries=3, delay=2, backoff=2, exceptions=(WebDriverException,))
def start(self) -> None:
    """
    Start the Chrome browser with the configured settings.
    
    Raises:
        BrowserError: If the browser fails to start
    """
    if self._is_running and self.driver is not None:
        self._logger.warning("Browser is already running")
        return
        
    try:
        self._logger.info("Starting Chrome browser...")
        
        # Set up Chrome options
        options = self._setup_chrome_options()
        
        # Get ChromeDriver path
        driver_path = self._get_chrome_driver_path()
        
        # Create Chrome service with the driver path
        self._service = ChromeService(executable_path=str(driver_path))
        
        # Initialize WebDriver
        self.driver = webdriver.Chrome(
            service=self._service,
            options=options
        )
        
        # Set window size if specified
        if self.config.window_size:
            self.driver.set_window_size(*self.config.window_size)
        else:
            self.driver.maximize_window()
        
        self._is_running = True
        self._logger.info("Chrome browser started successfully")
        
    except Exception as e:
        self._logger.error(f"Failed to start Chrome browser: {e}", exc_info=True)
        self._cleanup_resources()
        raise BrowserError(f"Failed to start Chrome browser: {e}") from e

# Add the stop method
def stop(self) -> None:
    """Stop the Chrome browser and clean up resources."""
    if not self._is_running or not self.driver:
        self._logger.warning("Browser is not running")
        return
        
    self._logger.info("Stopping Chrome browser...")
    self._cleanup_resources()
    self._logger.info("Browser stopped successfully")