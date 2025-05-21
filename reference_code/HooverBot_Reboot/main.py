import atexit
import glob
import logging
import os
import platform
import shutil
import sys
import tempfile
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException
)
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait, Select
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SERVERS = [
    {"username": "I11\\TOBOR", "campaign_values": ["710"]},
    {"username": "I10\\TOBOR", "campaign_values": ["990"]},
    {"username": "IB9\\TOBOR", "campaign_values": ["220"]},
    {"username": "IB8\\TOBOR", "campaign_values": ["750"]},
    {"username": "IBL\\TOBOR", "campaign_values": ["6400", "6700"]}  # IBL DNC Campaigns
]
PASSWORD = os.getenv("TELESERO_PASSWORD", "R0b0t!c47#")

def validate_phone_number(phone_number):
    """
    Validate and normalize a phone number.
    
    Args:
        phone_number (str): The phone number to validate
        
    Returns:
        str: Normalized phone number (digits only) or None if invalid
    """
    # Remove all non-digit characters
    cleaned = ''.join(c for c in phone_number if c.isdigit())
    
    # Check for valid US/Canada number (10 digits or 11 digits starting with 1)
    if len(cleaned) == 10:
        return cleaned
    elif len(cleaned) == 11 and cleaned[0] == '1':
        return cleaned[1:]  # Remove leading 1
    return None

def setup_logging():
    """Configure logging with both console and file handlers."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Set up logging format
    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)-8s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    
    # Create file handler with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"logs/hooverbot_{timestamp}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add our handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Disable unnecessary logging
    logging.getLogger('WDM').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    
    # Add separator for new run
    logging.info("=" * 50)
    logging.info(f"HooverBot started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Log file: {os.path.abspath(log_filename)}")
    logging.info("=" * 50)
    
    return log_filename

class ChromeManager:
    """Manages Chrome browser instances with clean profiles and automatic cleanup."""
    
    def __init__(self, headless=False):
        """Initialize Chrome with a fresh profile and automatic cleanup."""
        try:
            self.temp_profile_dir = tempfile.TemporaryDirectory()
            self.options = Options()
            
            # Store the temp dir name for process tracking
            self.temp_dir_name = os.path.basename(self.temp_profile_dir.name)
            
            # Configure Chrome options
            self.options.add_argument("--no-sandbox")
            self.options.add_argument("--disable-dev-shm-usage")
            self.options.add_argument(f"--user-data-dir={self.temp_profile_dir.name}")
            self.options.add_argument("--disable-extensions")
            self.options.add_argument("--disable-gpu")
            self.options.add_argument("--disable-application-cache")
            self.options.add_argument("--start-maximized")
            self.options.add_argument("--log-level=3")  # Suppress Chrome logging
            
            if headless:
                self.options.add_argument("--headless=new")
            
            # Set Chrome binary location if specified in environment
            chrome_path = os.getenv("CHROME_PATH")
            if chrome_path and os.path.exists(chrome_path):
                self.options.binary_location = chrome_path
            
            # Track our processes
            self._process_ids = set()
            
            # Ensure cleanup on exit
            atexit.register(self.cleanup)
            
            # Initialize webdriver
            self.driver = None
            self.service = None
            
            # Start the browser
            self.start()
            
        except Exception as e:
            logging.error(f"Failed to initialize Chrome browser: {str(e)}", exc_info=True)
            raise

    def start(self):
        """Start a new Chrome instance."""
        try:
            # Get ChromeDriver path
            driver_path = self._get_chromedriver_path()
            
            # Set up ChromeDriver service
            self.service = Service(driver_path)
            
            # Start Chrome with our options
            logging.info("Starting Chrome browser...")
            self.driver = webdriver.Chrome(service=self.service, options=self.options)
            
            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            # Track the process
            try:
                import psutil
                current_pid = os.getpid()
                current_process = psutil.Process(current_pid)
                children = current_process.children(recursive=True)
                
                for child in children:
                    try:
                        proc_name = child.name().lower()
                        if 'chrome' in proc_name or 'chromedriver' in proc_name:
                            self._process_ids.add(child.pid)
                            logging.debug(f"Tracked Chrome process: {child.pid} ({proc_name})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
            except Exception as e:
                logging.warning(f"Couldn't track Chrome processes: {e}")
            
            logging.info("Chrome browser started successfully")
            
        except Exception as e:
            logging.error(f"Failed to start Chrome browser: {str(e)}", exc_info=True)
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            raise
    
    def _get_chromedriver_path(self):
        """Get the correct ChromeDriver path with architecture handling."""
        try:
            # Use the ChromeDriverManager to get the appropriate driver
            driver_manager = ChromeDriverManager()
            driver_path = driver_manager.install()
            logging.info(f"Using ChromeDriver: {driver_path}")
            return driver_path
        except Exception as e:
            logging.error(f"Error getting ChromeDriver: {e}")
            raise
    
    def start(self):
        """Start a new Chrome instance."""
        self.driver = None
        self.service = None
        
        try:
            # Get ChromeDriver path first
            driver_path = self._get_chromedriver_path()
            
            # Set up ChromeDriver service with logging disabled
            self.service = Service(executable_path=driver_path, service_args=['--silent'])
            
            # Start Chrome with our options
            logging.info("Starting Chrome browser...")
            self.driver = webdriver.Chrome(service=self.service, options=self.options)
            
            # Set timeouts first to ensure they're in place
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            # Track the process after browser is successfully started
            try:
                import psutil
                current_pid = os.getpid()
                
                # Get all Chrome/ChromeDriver processes that are children of this process
                current_process = psutil.Process(current_pid)
                children = current_process.children(recursive=True)
                
                for child in children:
                    try:
                        proc_name = child.name().lower()
                        if 'chrome' in proc_name or 'chromedriver' in proc_name:
                            self._process_ids.add(child.pid)
                            logging.debug(f"Tracked Chrome process: {child.pid} ({proc_name})")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                        
            except Exception as e:
                logging.warning(f"Couldn't track Chrome processes: {e}")
            
            logging.info("Chrome browser started successfully")
            return self.driver
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Failed to start Chrome: {error_msg}")
            
            # Only perform minimal cleanup in case of failure
            try:
                if hasattr(self, 'driver') and self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                if hasattr(self, 'service') and self.service:
                    try:
                        self.service.stop()
                    except:
                        pass
            except Exception as cleanup_error:
                logging.error(f"Error during cleanup after failed start: {cleanup_error}")
                
            self.driver = None
            self.service = None
            return None
    
    def cleanup(self):
        """Clean up resources for this specific browser instance only."""
        try:
            # Close the browser window gracefully first
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                    logging.debug("Browser quit successfully")
                except Exception as e:
                    logging.error(f"Error closing browser: {e}")
                finally:
                    self.driver = None
            
            # Stop the ChromeDriver service
            if hasattr(self, 'service') and self.service:
                try:
                    self.service.stop()
                    logging.debug("ChromeDriver service stopped")
                except Exception as e:
                    logging.error(f"Error stopping service: {e}")
                finally:
                    self.service = None
            
            # Only attempt process cleanup if we have specific process IDs
            if hasattr(self, '_process_ids') and self._process_ids:
                try:
                    import psutil
                    current_pid = os.getpid()
                    
                    for pid in list(self._process_ids):
                        try:
                            proc = psutil.Process(pid)
                            
                            # Double-check this is actually our process
                            if proc.is_running():
                                # Get parent process to verify it's ours
                                parent = proc.parent()
                                if parent and parent.pid == current_pid:
                                    logging.debug(f"Terminating child process: {pid}")
                                    proc.terminate()
                                    try:
                                        proc.wait(timeout=3)
                                    except (psutil.TimeoutExpired, psutil.NoSuchProcess):
                                        pass
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                            logging.debug(f"Process {pid} already gone: {e}")
                            continue
                        except Exception as e:
                            logging.warning(f"Error terminating process {pid}: {e}")
                    
                    self._process_ids.clear()
                    
                except Exception as e:
                    logging.warning(f"Error during process cleanup: {e}")
            
            # Clean up the temp directory
            if hasattr(self, 'temp_profile_dir'):
                try:
                    if hasattr(self.temp_profile_dir, 'cleanup'):
                        self.temp_profile_dir.cleanup()
                        logging.debug("Temporary directory cleaned up")
                except Exception as e:
                    logging.error(f"Error cleaning up temp directory: {e}")
        
        except Exception as e:
            logging.error(f"Unexpected error during cleanup: {e}")
        finally:
            # Ensure we don't hold references to these objects
            if hasattr(self, 'driver') and self.driver is not None:
                self.driver = None
            if hasattr(self, 'service') and self.service is not None:
                self.service = None
                    
def _take_screenshot(driver, prefix):
    """
    Take a screenshot and save it with a timestamp.
    
    Args:
        driver: Selenium WebDriver instance
        prefix: Prefix for the screenshot filename
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"error_screenshot_{prefix}_{timestamp}.png"
    try:
        driver.save_screenshot(filename)
        logging.info(f"Screenshot saved as {filename}")
    except Exception as e:
        logging.error(f"Failed to take screenshot: {e}")

def login(driver, username, password):
    """Login to Telesero portal."""
    try:
        # Navigate to login page
        driver.get("https://portal.teleserosuite.com/login")
        
        # Wait for and enter username
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys(username)
        
        # Enter password
        driver.find_element(By.ID, "password").send_keys(password)
        
        # Click login button
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # Wait for successful login (monitoring page)
        WebDriverWait(driver, 20).until(
            EC.url_contains("/contact-center/monitoring")
        )
        logging.info(f"Successfully logged in as {username}")
        return True
    except Exception as e:
        logging.error(f"Login failed for {username}: {str(e)}")
        return False

def add_to_blacklist(driver, phone_number, max_retries=2):
    """
    Add phone number to blacklist with retry logic and improved success detection.
    
    Args:
        driver: Selenium WebDriver instance
        phone_number: Phone number to add to blacklist
        max_retries: Maximum number of retry attempts
        
    Returns:
        tuple: (success: bool, message: str) - Status and message of the operation
    """
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Attempt {attempt}/{max_retries} to add {phone_number} to blacklist")
            
            # Navigate to blacklist page
            driver.get("https://portal.teleserosuite.com/contact-center/blacklist/new")
            
            # Wait for page to load completely
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Try multiple ways to find the phone input
            try:
                # First try by ID
                phone_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "vicidial_filter_phone_number_type_fullPhoneNumber"))
                )
            except:
                # Try by name
                try:
                    phone_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.NAME, "phoneNumber"))
                    )
                except:
                    # Try by CSS selector
                    try:
                        phone_input = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='tel'], input[type='text']"))
                        )
                    except Exception as e:
                        raise Exception(f"Could not find phone input: {e}")
            
            # Clear and type phone number
            phone_input.clear()
            phone_input.send_keys(phone_number)
            
            # Try multiple ways to find the submit button
            try:
                # First try by text
                submit_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add to Blacklist') or contains(text(), 'Add') or contains(text(), 'Submit') or contains(text(), 'Save')]"))
                )
            except:
                # Try by class
                try:
                    submit_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "submit-button"))
                    )
                except:
                    # Try by type
                    try:
                        submit_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
                        )
                    except Exception as e:
                        raise Exception(f"Could not find submit button: {e}")
            
            # Click submit button
            submit_button.click()
            
            # Wait for success/error message
            try:
                # Wait for success message
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
                )
                logging.info(f"✓ Successfully added {phone_number} to blacklist")
                return True, f"Successfully added {phone_number} to blacklist"
                
            except TimeoutException:
                # Check for error messages
                try:
                    error_elements = driver.find_elements(By.CSS_SELECTOR, ".error-message, .alert-danger, .toast-error, .error")
                    for error in error_elements:
                        if error.is_displayed():
                            error_text = error.text.strip()
                            if error_text:
                                # Treat "already listed" as success
                                if "already" in error_text.lower() or "exists" in error_text.lower():
                                    logging.info(f"✓ Number already in blacklist: {error_text}")
                                    return True, f"Number already in blacklist: {error_text}"
                                logging.error(f"Blacklist error: {error_text}")
                                return False, f"Blacklist error: {error_text}"
                except:
                    pass
                
                # If we get here, we didn't find any messages
                logging.error("No success/error message found after submission")
                if attempt < max_retries:
                    logging.info(f"Retrying attempt {attempt + 1}...")
                    continue
                return False, "No success/error message found after submission"
            
        except Exception as e:
            logging.error(f"Error in blacklist attempt {attempt}: {str(e)}")
            if attempt == max_retries:
                _take_screenshot(driver, "blacklist_final_error")
                return False, f"Failed to add {phone_number} to blacklist: {str(e)}"
            
            # Wait before retrying
            time.sleep(2 * attempt)
            continue
    
    return False, "Max retries reached for blacklist operation"

def add_to_dnc(driver, phone_number, campaign_value, max_retries=2):
    """
    Add phone number to DNC list with retry logic and improved success detection.
    
    Args:
        driver: Selenium WebDriver instance
        phone_number: Phone number to add to DNC
        campaign_value: Campaign value to add the number to
        max_retries: Maximum number of retry attempts
        
    Returns:
        tuple: (success: bool, message: str) - Status and message of the operation
    """
    dnc_url = "https://portal.teleserosuite.com/contact-center/dnc/text"
    
    for attempt in range(1, max_retries + 1):
        try:
            logging.info(f"Attempt {attempt}/{max_retries} to add {phone_number} to DNC campaign {campaign_value}")
            
            # Navigate to DNC page
            driver.get(dnc_url)
            
            # Wait for page to load completely
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for phone input
            phone_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "vicidial_dnc_text_type_numbers"))
            )
            phone_input.clear()
            
            # Type phone number
            for char in str(phone_number):
                phone_input.send_keys(char)
                time.sleep(0.1)
            
            # Wait for campaign selection
            try:
                # First try the expected ID
                campaign_select = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "vicidial_dnc_text_type_campaignId"))
                )
            except TimeoutException:
                # If not found, try alternative IDs
                try:
                    campaign_select = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "campaignId"))
                    )
                except TimeoutException:
                    # If still not found, try locating by name
                    campaign_select = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.NAME, "campaignId"))
                    )
            
            # Use Select class to handle the dropdown
            select = Select(campaign_select)
            select.select_by_value(str(campaign_value))
            
            # Click add button
            submit_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            submit_btn.click()
            
            # Wait for the response message
            try:
                # Wait for any alert to appear
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".alert"))
                )
                
                # Check for success message
                success_alerts = driver.find_elements(By.CSS_SELECTOR, ".alert-success")
                if success_alerts:
                    for alert in success_alerts:
                        if alert.is_displayed():
                            success_text = alert.text.strip()
                            if "Processed" in success_text and "numbers" in success_text:
                                logging.info(f"DNC success: {success_text}")
                                return True, success_text
                
                # Check for 'already in DNC' message
                exists_alerts = driver.find_elements(By.CSS_SELECTOR, ".alert-danger")
                for alert in exists_alerts:
                    if alert.is_displayed():
                        text = alert.text.strip().lower()
                        if "already" in text:
                            exists_text = alert.text.strip()
                            logging.info(f"Number already in DNC: {exists_text}")
                            return True, exists_text
                
                # Check for other error messages
                error_alerts = driver.find_elements(By.CSS_SELECTOR, ".alert-danger")
                if error_alerts:
                    for alert in error_alerts:
                        if alert.is_displayed():
                            error_text = alert.text.strip()
                            logging.warning(f"DNC error: {error_text}")
                            if attempt < max_retries:
                                time.sleep(2)
                                continue
                            return False, error_text
                
                # If we get here, no recognized message was found
                logging.warning("No recognized success/error message found after DNC submission")
                return False, "No clear success or error message detected"
                
            except TimeoutException:
                logging.warning("Timed out waiting for DNC response message")
                return False, "Timed out waiting for response"
            
        except Exception as e:
            error_msg = f"Error during DNC form submission (attempt {attempt}): {str(e)}"
            logging.error(error_msg, exc_info=True)
            
            # Take screenshot on any error
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"dnc_error_{campaign_value}_{timestamp}.png"
            try:
                driver.save_screenshot(screenshot_path)
                logging.info(f"Screenshot saved: {screenshot_path}")
            except Exception as screenshot_error:
                logging.error(f"Failed to save screenshot: {screenshot_error}")
                
            if attempt >= max_retries:
                return False, error_msg
            
            time.sleep(2)
            continue
    
    return False, "Max retries reached without success"

def reset_browser(driver, force_logout=False):
    """
    Reset browser state between server processing.
    
    Args:
        driver: Selenium WebDriver instance
        force_logout: If True, explicitly log out before resetting
    """
    try:
        # If we need to explicitly log out first
        if force_logout:
            try:
                # Try to navigate to logout URL if it exists
                driver.get("https://portal.teleserosuite.com/logout")
                time.sleep(2)  # Give it time to log out
            except:
                pass
        
        # Clear cookies and local storage
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        
        # Navigate to a blank page to clear any existing state
        driver.get("about:blank")
        
        # Wait for the blank page to load
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Clear any remaining alerts
        try:
            driver.execute_script("""
                try { 
                    window.sessionStorage.clear(); 
                } catch(e) {}
            """)
        except Exception as e:
            logging.warning(f"Could not clear storage: {e}")
        
        # Dismiss any alerts
        try:
            alert = driver.switch_to.alert
            alert.dismiss()
        except:
            pass
            
        # Clear any lingering alerts or prompts
        try:
            driver.execute_script("window.onbeforeunload = null;")
            driver.execute_script("window.onunload = null;")
        except:
            pass
            
        return True
    except Exception as e:
        logging.warning(f"Error resetting browser: {e}")
        # Try a more aggressive reset if the first one fails
        try:
            driver.get("about:blank")
            return True
        except:
            return False

def process_server(driver, server_info, phone_number):
    """
    Process a single server using the shared browser instance.
    
    Args:
        driver: Selenium WebDriver instance
        server_info: Dictionary containing server info (username, campaign_values)
        phone_number: Phone number to process
        
    Returns:
        tuple: (bool, str) - Success status and message
    """
    username = server_info["username"]
    campaign_values = server_info["campaign_values"]
    
    if not isinstance(campaign_values, list):
        campaign_values = [campaign_values]
    
    try:
        # Reset browser state before starting
        if not reset_browser(driver, force_logout=True):
            logging.warning("Browser reset had issues, continuing anyway...")
        
        # Set reasonable timeouts
        driver.set_page_load_timeout(45)
        driver.set_script_timeout(30)
        driver.implicitly_wait(10)
        
        # Step 1: Login
        logging.info(f"\n--- Login to {username} ---")
        if not login(driver, username, PASSWORD):
            error_msg = f"Login failed for {username}"
            logging.error(error_msg)
            return False, error_msg
        
        # Small delay after login
        time.sleep(1)
        
        # Step 2: Add to blacklist
        logging.info("Adding to Blacklist...")
        blacklist_success, blacklist_msg = add_to_blacklist(driver, phone_number)
        
        # Check if blacklist operation was successful
        if not blacklist_success:
            # If the number is already blacklisted, that's actually a success case
            if "already in blacklist" in blacklist_msg.lower():
                logging.info(f"Number already in blacklist: {blacklist_msg}")
                blacklist_success = True
            else:
                error_msg = f"Blacklist failed: {blacklist_msg}"
                logging.error(error_msg)
                return False, error_msg
        
        logging.info(f"Successfully processed blacklist for {phone_number}")
        
        # Process each campaign for this server
        campaign_results = []
        for campaign_value in campaign_values:
            campaign_success = False
            campaign_msg = f"Campaign {campaign_value}"
            
            try:
                logging.info(f"Processing DNC for campaign {campaign_value}...")
                
                # Navigate to DNC page for this campaign
                try:
                    driver.get("https://portal.teleserosuite.com/contact-center/dnc/text")
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.ID, "vicidial_dnc_text_type_campaignId"))
                    )
                except Exception as e:
                    error_msg = f"Failed to navigate to DNC page for campaign {campaign_value}: {str(e)}"
                    logging.error(error_msg)
                    campaign_results.append((campaign_value, False, error_msg))
                    continue
                
                # Add to DNC for this campaign
                dnc_success, dnc_msg = add_to_dnc(driver, phone_number, campaign_value)
                
                # Take a screenshot after DNC operation
                screenshot_path = _take_screenshot(driver, f"dnc_result_{campaign_value}")
                
                # Check DNC operation result
                if dnc_success:
                    campaign_success = True
                    campaign_msg = f"Successfully added to DNC campaign {campaign_value}"
                    logging.info(campaign_msg)
                else:
                    campaign_msg = f"Failed to add to DNC campaign {campaign_value}: {dnc_msg}"
                    logging.error(campaign_msg)
                
            except Exception as e:
                error_msg = f"Error processing campaign {campaign_value}: {str(e)}"
                logging.error(error_msg, exc_info=True)
                campaign_msg = error_msg
                
            finally:
                campaign_results.append((campaign_value, campaign_success, campaign_msg))
                # Small delay between campaign processing
                time.sleep(1)
        
        # Check if all campaigns were successful
        all_success = all(success for _, success, _ in campaign_results)
        
        # Generate summary message
        if all_success:
            summary = f"Successfully processed all {len(campaign_results)} campaign(s) for {username}"
        else:
            success_count = sum(1 for _, success, _ in campaign_results if success)
            summary = f"Processed {success_count}/{len(campaign_results)} campaigns successfully for {username}"
        
        # Add campaign details to the summary
        for i, (campaign, success, msg) in enumerate(campaign_results, 1):
            status = "✓" if success else "✗"
            summary += f"\n  {i}. {status} {msg}"
        
        return all_success, summary
        
    except Exception as e:
        error_msg = f"Error processing {username}: {str(e)}"
        logging.error(error_msg, exc_info=True)
        
        # Take screenshot on error
        _take_screenshot(driver, f"error_{username}")
            
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Error processing {username}: {str(e)}"
        logging.error(error_msg, exc_info=True)
        
        # Take screenshot on error
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"error_{username}_{campaign_value}_{timestamp}.png"
            driver.save_screenshot(screenshot_path)
            logging.info(f"Screenshot saved to {screenshot_path}")
        except Exception as screenshot_error:
            logging.error(f"Failed to take screenshot: {screenshot_error}")
            
        return False, str(e)

def cleanup_system():
    """Clean up system resources and old files."""
    try:
        # Clean up old chromedriver files in the current directory only
        current_dir = os.getcwd()
        for f in glob.glob(os.path.join(current_dir, "chromedriver*")):
            try:
                if os.path.isfile(f):
                    os.remove(f)
                    logging.info(f"Removed old chromedriver: {f}")
            except Exception as e:
                logging.warning(f"Could not remove {f}: {e}")
        
        # Don't clear the entire wdm cache, just old versions
        try:
            wdm_cache = os.path.expanduser("~/.wdm")
            if os.path.exists(wdm_cache):
                # Only remove old driver versions, keep the current one
                for root, dirs, files in os.walk(wdm_cache):
                    for d in dirs[:]:
                        if d.startswith('drivers'):
                            driver_path = os.path.join(root, d)
                            try:
                                # Keep the most recent version
                                versions = sorted(os.listdir(driver_path), reverse=True)
                                for version in versions[1:]:  # Keep the first (newest) version
                                    old_version = os.path.join(driver_path, version)
                                    shutil.rmtree(old_version, ignore_errors=True)
                                    logging.info(f"Cleared old webdriver version: {version}")
                            except Exception as e:
                                logging.warning(f"Could not clean up webdriver versions: {e}")
        except Exception as e:
            logging.warning(f"Error cleaning webdriver cache: {e}")
            
    except Exception as e:
        logging.warning(f"Error during system cleanup: {e}")
    
    # Don't kill any Chrome processes - let the user manage their own browser

def main():
    """
    Main function to run the script.
    
    Handles phone number processing and manages the browser instance.
    """
    # Set up logging
    log_filename = setup_logging()
    
    try:
        # Get phone number from command line or prompt user
        if len(sys.argv) > 1:
            phone_number = sys.argv[1]
        else:
            print("Please enter a 10-digit phone number (no symbols or spaces):")
            phone_number = input("Phone number: ").strip()
            
        # Validate phone number
        if not phone_number.isdigit() or len(phone_number) != 10:
            print(f"Invalid phone number: {phone_number}")
            print("Please provide a 10-digit number without any symbols or spaces.")
            print("Example: 1234567890")
            sys.exit(1)
            
        logging.info(f"\nProcessing phone number: {phone_number}")
        
        # Initialize ChromeManager
        chrome_manager = ChromeManager(headless=False)
        driver = chrome_manager.driver
        
        if not driver:
            logging.error("Failed to initialize Chrome browser")
            sys.exit(1)  # Exit with error code since browser failed to start
        
        # Process each server using process_server function
        for server_info in SERVERS:
            username = server_info["username"]
            logging.info(f"\nProcessing server: {username}")
            
            # Process the server
            success, message = process_server(driver, server_info, phone_number)
            
            if success:
                logging.info(f"✓ Successfully processed {username}")
                logging.info(message)
            else:
                logging.error(f"✗ Failed to process {username}")
                logging.error(message)
            
            # Small delay between servers
            time.sleep(2)
        
        logging.info("\nAll servers processed successfully!")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # Clean up
        if 'driver' in locals():
            driver.quit()
        logging.info("Script completed.\n")
        logging.info("Log file location:")
        logging.info(os.path.abspath(log_filename))
        logging.info("=" * 50)
        
        # Clean up system resources
        cleanup_system()
        logging.info(f"HooverBot finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("="*50 + "\n")
        print("\nThank you for using HooverBot. Goodbye! 👋\n")

if __name__ == "__main__":
    main()
