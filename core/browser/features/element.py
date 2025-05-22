"""Element handling and interactions."""
from typing import Optional, List, Union, Tuple, Dict, Any, Callable
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
    TimeoutException
)

from ..exceptions import (
    ElementNotFoundError,
    ElementNotInteractableError,
    TimeoutError as BrowserTimeoutError
)

class ElementHelper:
    """Helper class for web element interactions."""
    
    def __init__(self, browser: Any):
        """Initialize with a browser instance.
        
        Args:
            browser: The browser instance (must have a 'driver' attribute)
        """
        self.browser = browser
        self.driver = browser.driver
        self.logger = getattr(browser, '_logger', None)
    
    def _log(self, level: str, message: str, *args, **kwargs) -> None:
        """Log a message if logger is available."""
        if self.logger:
            getattr(self.logger, level)(message, *args, **kwargs)
    
    def find_element(
        self,
        by: str = By.ID,
        value: Optional[str] = None,
        timeout: Optional[float] = None,
        parent: Optional[WebElement] = None
    ) -> WebElement:
        """Find a single web element.
        
        Args:
            by: Locator strategy (e.g., By.ID, By.CSS_SELECTOR)
            value: The locator value
            timeout: Maximum time to wait for the element
            parent: Optional parent element to search within
            
        Returns:
            WebElement: The found web element
            
        Raises:
            ElementNotFoundError: If the element is not found
        """
        if not value:
            raise ValueError("Value cannot be empty")
            
        try:
            if timeout is not None and timeout > 0:
                wait = WebDriverWait(
                    self.driver if parent is None else parent,
                    timeout
                )
                return wait.until(EC.presence_of_element_located((by, value)))
            
            if parent is not None:
                return parent.find_element(by, value)
            return self.driver.find_element(by, value)
            
        except (NoSuchElementException, TimeoutException) as e:
            self._log('debug', f"Element not found: {by}={value}")
            raise ElementNotFoundError(f"Element not found: {by}={value}") from e
        except StaleElementReferenceException as e:
            self._log('debug', f"Stale element reference: {by}={value}")
            raise ElementNotFoundError(f"Stale element reference: {by}={value}") from e
    
    def find_elements(
        self,
        by: str = By.ID,
        value: Optional[str] = None,
        timeout: Optional[float] = None,
        parent: Optional[WebElement] = None
    ) -> List[WebElement]:
        """Find multiple web elements.
        
        Args:
            by: Locator strategy (e.g., By.ID, By.CSS_SELECTOR)
            value: The locator value
            timeout: Maximum time to wait for at least one element
            parent: Optional parent element to search within
            
        Returns:
            List[WebElement]: List of found web elements (empty if none found)
        """
        if not value:
            return []
            
        try:
            if timeout is not None and timeout > 0:
                wait = WebDriverWait(
                    self.driver if parent is None else parent,
                    timeout
                )
                return wait.until(
                    EC.presence_of_all_elements_located((by, value))
                )
            
            if parent is not None:
                return parent.find_elements(by, value)
            return self.driver.find_elements(by, value)
            
        except (NoSuchElementException, TimeoutException):
            return []
        except StaleElementReferenceException:
            return []
    
    def wait_for_element_visible(
        self,
        by: str = By.ID,
        value: Optional[str] = None,
        timeout: float = 10.0
    ) -> WebElement:
        """Wait for an element to be visible.
        
        Args:
            by: Locator strategy
            value: The locator value
            timeout: Maximum time to wait
            
        Returns:
            WebElement: The visible web element
            
        Raises:
            TimeoutError: If element is not visible within timeout
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.visibility_of_element_located((by, value)))
        except TimeoutException as e:
            raise BrowserTimeoutError(
                f"Element not visible after {timeout} seconds: {by}={value}"
            ) from e
    
    def wait_for_element_clickable(
        self,
        by: str = By.ID,
        value: Optional[str] = None,
        timeout: float = 10.0
    ) -> WebElement:
        """Wait for an element to be clickable.
        
        Args:
            by: Locator strategy
            value: The locator value
            timeout: Maximum time to wait
            
        Returns:
            WebElement: The clickable web element
            
        Raises:
            TimeoutError: If element is not clickable within timeout
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException as e:
            raise BrowserTimeoutError(
                f"Element not clickable after {timeout} seconds: {by}={value}"
            ) from e
    
    def click(
        self,
        by: str = By.ID,
        value: Optional[str] = None,
        element: Optional[WebElement] = None,
        timeout: Optional[float] = None
    ) -> None:
        """Click on an element.
        
        Args:
            by: Locator strategy (required if element is None)
            value: The locator value (required if element is None)
            element: Optional element to click (alternative to locator)
            timeout: Maximum time to wait for element to be clickable
            
        Raises:
            ElementNotInteractableError: If the element is not interactable
        """
        target = element or self.find_element(by, value, timeout=timeout)
        
        try:
            if timeout is not None and timeout > 0:
                target = self.wait_for_element_clickable(
                    by=by,
                    value=value,
                    timeout=timeout
                )
            
            target.click()
            
        except (ElementClickInterceptedException, ElementNotInteractableException) as e:
            self._log('debug', f"Element not interactable: {str(e)}")
            raise ElementNotInteractableError(
                f"Element not interactable: {by}={value if value else 'element'}"
            ) from e
    
    def send_keys(
        self,
        text: str,
        by: str = By.ID,
        value: Optional[str] = None,
        element: Optional[WebElement] = None,
        clear_first: bool = True,
        timeout: Optional[float] = None
    ) -> None:
        """Send keys to an element (input field, textarea, etc.).
        
        Args:
            text: Text to send
            by: Locator strategy (required if element is None)
            value: The locator value (required if element is None)
            element: Optional element to send keys to (alternative to locator)
            clear_first: Whether to clear the field before sending keys
            timeout: Maximum time to wait for element to be interactable
            
        Raises:
            ElementNotInteractableError: If the element is not interactable
        """
        target = element or self.find_element(by, value, timeout=timeout)
        
        try:
            if timeout is not None and timeout > 0:
                target = self.wait_for_element_visible(
                    by=by,
                    value=value,
                    timeout=timeout
                )
            
            if clear_first:
                target.clear()
            
            target.send_keys(text)
            
        except (ElementNotInteractableException, StaleElementReferenceException) as e:
            self._log('debug', f"Element not interactable: {str(e)}")
            raise ElementNotInteractableError(
                f"Element not interactable: {by}={value if value else 'element'}"
            ) from e
    
    def get_text(
        self,
        by: str = By.ID,
        value: Optional[str] = None,
        element: Optional[WebElement] = None,
        timeout: Optional[float] = None
    ) -> str:
        """Get the text content of an element.
        
        Args:
            by: Locator strategy (required if element is None)
            value: The locator value (required if element is None)
            element: Optional element to get text from (alternative to locator)
            timeout: Maximum time to wait for element to be present
            
        Returns:
            str: The text content of the element
        """
        target = element or self.find_element(by, value, timeout=timeout)
        
        try:
            if timeout is not None and timeout > 0:
                target = self.wait_for_element_visible(
                    by=by,
                    value=value,
                    timeout=timeout
                )
            
            return target.text
            
        except StaleElementReferenceException as e:
            self._log('debug', f"Stale element reference: {str(e)}")
            raise ElementNotFoundError("Element is no longer attached to the DOM") from e
    
    def is_displayed(
        self,
        by: str = By.ID,
        value: Optional[str] = None,
        element: Optional[WebElement] = None,
        timeout: Optional[float] = 0
    ) -> bool:
        """Check if an element is displayed.
        
        Args:
            by: Locator strategy (required if element is None)
            value: The locator value (required if element is None)
            element: Optional element to check (alternative to locator)
            timeout: Maximum time to wait for element to be present (0 for immediate check)
            
        Returns:
            bool: True if the element is displayed, False otherwise
        """
        try:
            if element is None and (by is None or value is None):
                raise ValueError("Either element or both by and value must be provided")
                
            if element is not None:
                return element.is_displayed()
                
            if timeout and timeout > 0:
                try:
                    element = self.wait_for_element_visible(by, value, timeout)
                    return element.is_displayed()
                except (BrowserTimeoutError, ElementNotFoundError):
                    return False
            
            element = self.find_element(by, value, timeout=0)
            return element.is_displayed()
            
        except (NoSuchElementException, StaleElementReferenceException):
            return False
