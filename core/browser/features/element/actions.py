"""Element interaction actions."""
from typing import Any, Optional
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    ElementNotInteractableException,
    ElementClickInterceptedException,
    StaleElementReferenceException
)

from ..exceptions import ElementNotInteractableError

class ElementActionsMixin:
    """Mixin class providing element interaction methods."""
    
    def click_element(self, element: WebElement) -> None:
        """Click on an element with error handling.
        
        Args:
            element: The WebElement to click
            
        Raises:
            ElementNotInteractableError: If the element is not interactable
        """
        try:
            element.click()
        except (ElementNotInteractableException, ElementClickInterceptedException) as e:
            raise ElementNotInteractableError("Element is not interactable") from e
    
    def send_keys_to_element(self, element: WebElement, keys: str) -> None:
        """Send keys to an element with error handling.
        
        Args:
            element: The WebElement to send keys to
            keys: The keys to send
            
        Raises:
            ElementNotInteractableError: If the element is not interactable
        """
        try:
            element.clear()
            element.send_keys(keys)
        except (ElementNotInteractableException, StaleElementReferenceException) as e:
            raise ElementNotInteractableError("Cannot send keys to element") from e
    
    def get_element_text(self, element: WebElement) -> str:
        """Get text from an element with error handling.
        
        Args:
            element: The WebElement to get text from
            
        Returns:
            The text content of the element
            
        Raises:
            ElementNotInteractableError: If the element is not visible
        """
        try:
            return element.text
        except StaleElementReferenceException as e:
            raise ElementNotInteractableError("Element is not attached to the DOM") from e
    
    def get_element_attribute(self, element: WebElement, name: str) -> Optional[str]:
        """Get an attribute from an element with error handling.
        
        Args:
            element: The WebElement to get the attribute from
            name: The name of the attribute
            
        Returns:
            The attribute value or None if not found
            
        Raises:
            ElementNotInteractableError: If the element is not visible
        """
        try:
            return element.get_attribute(name)
        except StaleElementReferenceException as e:
            raise ElementNotInteractableError("Element is not attached to the DOM") from e
    
    def is_element_displayed(self, element: WebElement) -> bool:
        """Check if an element is displayed with error handling.
        
        Args:
            element: The WebElement to check
            
        Returns:
            True if the element is displayed, False otherwise
        """
        try:
            return element.is_displayed()
        except StaleElementReferenceException:
            return False
    
    def is_element_enabled(self, element: WebElement) -> bool:
        """Check if an element is enabled with error handling.
        
        Args:
            element: The WebElement to check
            
        Returns:
            True if the element is enabled, False otherwise
        """
        try:
            return element.is_enabled()
        except StaleElementReferenceException:
            return False
