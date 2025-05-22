"""Base classes for element interactions."""
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union, Dict
from selenium.webdriver.remote.webelement import WebElement

class BaseElement(ABC):
    """Base class for web element wrappers."""
    
    def __init__(self, element: WebElement):
        """Initialize with a Selenium WebElement.
        
        Args:
            element: The Selenium WebElement to wrap
        """
        self._element = element
    
    @property
    def element(self) -> WebElement:
        """Get the underlying Selenium WebElement."""
        return self._element
    
    @abstractmethod
    def click(self) -> None:
        """Click the element."""
        pass
    
    @abstractmethod
    def get_attribute(self, name: str) -> Optional[str]:
        """Get an attribute value from the element.
        
        Args:
            name: Name of the attribute to get
            
        Returns:
            The attribute value or None if not found
        """
        pass
    
    @abstractmethod
    def is_displayed(self) -> bool:
        """Check if the element is displayed."""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if the element is enabled."""
        pass
    
    @abstractmethod
    def send_keys(self, value: str) -> None:
        """Send keys to the element.
        
        Args:
            value: The text to send to the element
        """
        pass
    
    @abstractmethod
    def text(self) -> str:
        """Get the text content of the element."""
        pass
