"""
browser_utils.py
Abstraction for robust Selenium WebDriver setup with enhanced viewport management.
Supports fallback logic, stealth automation, and centralized logging.
"""
import os
import logging
import time
import random
from urllib.parse import urlparse, urljoin
from typing import Tuple, Optional, Dict, Any, Union
from enum import Enum

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    WebDriverException,
    StaleElementReferenceException,
    ElementNotInteractableException
)
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScrollDirection(Enum):
    """Direction for smooth scrolling."""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

class ViewportState:
    """Maintains viewport state and provides viewport-aware operations."""
    
    def __init__(self, driver):
        self.driver = driver
        self._last_viewport_size = (0, 0)
        self._update_viewport_size()
    
    def _update_viewport_size(self) -> None:
        """Update the cached viewport size."""
        try:
            self._last_viewport_size = (
                self.driver.execute_script("return window.innerWidth"),
                self.driver.execute_script("return window.innerHeight")
            )
        except WebDriverException as e:
            logger.warning(f"Failed to update viewport size: {e}")
    
    @property
    def size(self) -> Tuple[int, int]:
        """Get the current viewport size."""
        self._update_viewport_size()
        return self._last_viewport_size
    
    @property
    def width(self) -> int:
        """Get the current viewport width."""
        return self.size[0]
    
    @property
    def height(self) -> int:
        """Get the current viewport height."""
        return self.size[1]
    
    def is_point_visible(self, x: int, y: int, margin: int = 5) -> bool:
        """Check if a point is within the visible viewport."""
        width, height = self.size
        return (
            margin <= x <= (width - margin) and
            margin <= y <= (height - margin)
        )
    
    def is_element_in_viewport(self, element: WebElement, margin: int = 5) -> bool:
        """Check if an element is within the visible viewport."""
        try:
            rect = element.rect
            element_top = rect['y']
            element_bottom = element_top + rect['height']
            element_left = rect['x']
            element_right = element_left + rect['width']
            
            viewport_width, viewport_height = self.size
            
            return (
                element_top >= -margin and
                element_left >= -margin and
                element_bottom <= (viewport_height + margin) and
                element_right <= (viewport_width + margin)
            )
        except (StaleElementReferenceException, WebDriverException) as e:
            logger.warning(f"Failed to check element visibility: {e}")
            return False
    
    def ensure_element_visible(
        self, 
        element: WebElement, 
        max_attempts: int = 3,
        scroll_margin: int = 50
    ) -> bool:
        """Ensure an element is visible in the viewport with smooth scrolling."""
        for attempt in range(max_attempts):
            try:
                if self.is_element_in_viewport(element, scroll_margin):
                    return True
                
                # Scroll element into view with smooth behavior
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({"
                    "  behavior: 'smooth',"
                    f"  block: 'center',"
                    f"  inline: 'nearest',"
                    f"  margin: {scroll_margin}"
                    "});",
                    element
                )
                
                # Add some jitter to the wait time
                time.sleep(0.5 + random.uniform(0, 0.3))
                
                # Double check visibility
                if self.is_element_in_viewport(element, scroll_margin):
                    return True
                    
            except (StaleElementReferenceException, WebDriverException) as e:
                logger.warning(f"Attempt {attempt + 1} to make element visible failed: {e}")
                if attempt == max_attempts - 1:  # Last attempt
                    return False
                
                time.sleep(0.5)
        
        return False
    
    def smooth_scroll(
        self, 
        direction: ScrollDirection = ScrollDirection.DOWN,
        distance: Optional[int] = None,
        duration: float = 0.5,
        steps: int = 20
    ) -> None:
        """Smoothly scroll the viewport in the specified direction."""
        if distance is None:
            distance = self.height // 2  # Default to half viewport height
        
        # Ensure distance is reasonable
        distance = max(10, min(distance, self.height * 2))
        
        # Calculate scroll amounts based on direction
        if direction == ScrollDirection.UP:
            scroll_x, scroll_y = 0, -distance
        elif direction == ScrollDirection.DOWN:
            scroll_x, scroll_y = 0, distance
        elif direction == ScrollDirection.LEFT:
            scroll_x, scroll_y = -distance, 0
        else:  # RIGHT
            scroll_x, scroll_y = distance, 0
        
        # Generate smooth scroll steps
        step_duration = duration / steps
        
        for i in range(1, steps + 1):
            # Ease-in-out easing function
            t = i / steps
            ease = t * t * (3 - 2 * t)
            
            # Calculate current scroll position
            current_x = int(scroll_x * ease)
            current_y = int(scroll_y * ease)
            
            # Scroll by the delta
            self.driver.execute_script(
                f"window.scrollBy({current_x}, {current_y});"
            )
            
            # Add some randomness to the timing
            time.sleep(step_duration * random.uniform(0.8, 1.2))

def wait_for_page_load(driver, timeout=30):
    """Wait for the page to completely load."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        return True
    except TimeoutException:
        logger.warning(f"Page load timed out after {timeout} seconds")
        return False

def wait_for_url_contains(driver, text, timeout=30):
    """Wait until the current URL contains the specified text."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: text in d.current_url
        )
        return True
    except TimeoutException:
        logger.warning(f"URL did not contain '{text}' after {timeout} seconds")
        return False

def wait_for_url_change(driver, original_url, timeout=30):
    """Wait until the URL changes from the original URL."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.current_url != original_url
        )
        return True
    except TimeoutException:
        logger.warning(f"URL did not change from '{original_url}' after {timeout} seconds")
        return False

def safe_get(driver, url, timeout=30):
    """Safely navigate to a URL with error handling and page load verification."""
    try:
        original_url = driver.current_url
        logger.info(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for page load and URL change
        if not wait_for_page_load(driver, timeout):
            logger.warning("Page load verification failed, but continuing...")
            
        # Verify we're on the expected domain
        expected_domain = urlparse(url).netloc
        current_domain = urlparse(driver.current_url).netloc
        
        if expected_domain and expected_domain not in current_domain:
            logger.warning(f"Expected domain '{expected_domain}' but got '{current_domain}'")
            return False
            
        return True
        
    except WebDriverException as e:
        logger.error(f"Error navigating to {url}: {e}")
        return False

def is_element_visible(driver, by, value, timeout=10):
    """Check if an element is visible on the page."""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )
        return element is not None
    except TimeoutException:
        return False

def create_driver(use_uc=None, headless=False, disable_infobars=True):
    """
    Create and configure a Chrome WebDriver instance with enhanced options.
    
    Args:
        use_uc (bool): Use undetected-chromedriver for stealth automation
        headless (bool): Run in headless mode
        disable_infobars (bool): Disable Chrome infobars
        
    Returns:
        WebDriver: Configured Chrome WebDriver instance
    """
    # Initialize Chrome options
    options = webdriver.ChromeOptions()
    if disable_infobars:
        options.add_argument("--disable-infobars")
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
    
    # Common arguments
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    use_uc_env = os.getenv("USE_UC", "0").lower() in ("1", "true", "yes")
    if use_uc is None:
        use_uc = use_uc_env
        
    if use_uc:
        try:
            import undetected_chromedriver as uc
            driver = uc.Chrome(options=options)
            driver.implicitly_wait(5)
            logger.info("[browser_utils] Using undetected-chromedriver (uc) for stealth automation.")
            return driver
        except ImportError:
            logger.warning("[browser_utils] undetected-chromedriver not installed. Falling back to standard ChromeDriver.")
        except Exception as e:
            logger.warning(f"[browser_utils] Could not launch undetected-chromedriver: {e}. Falling back to standard ChromeDriver.")
    
    # Check CHROMEDRIVER_PATH environment variable
    chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
    if chromedriver_path and os.path.exists(chromedriver_path):
        logging.info(f"[browser_utils] Trying ChromeDriver from CHROMEDRIVER_PATH: {chromedriver_path}")
        try:
            driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
            driver.implicitly_wait(5)
            return driver
        except WebDriverException as e:
            logging.error(f"Failed to launch ChromeDriver from {chromedriver_path}. Error: {str(e)}")
    
    # Check for chromedriver.exe in assets directory
    assets_driver = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'chromedriver.exe')
    if os.path.exists(assets_driver):
        logging.info(f"[browser_utils] Trying ChromeDriver from assets directory: {assets_driver}")
        try:
            driver = webdriver.Chrome(service=Service(assets_driver), options=options)
            driver.implicitly_wait(5)
            return driver
        except WebDriverException as e:
            logging.error(f"Failed to launch ChromeDriver from assets directory. Error: {str(e)}")
    
    # Fallback to webdriver_manager
    try:
        logging.info("[browser_utils] Falling back to webdriver_manager ChromeDriver.")
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service as ChromeService
        
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.implicitly_wait(5)
        return driver
    except Exception as e:
        logging.error(f"Could not launch ChromeDriver with webdriver_manager: {e}")
        raise
