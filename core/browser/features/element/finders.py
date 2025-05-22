"""Element finding functionality."""
from typing import List, Optional, Tuple, Union, Any, Dict
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class ElementFindersMixin:
    """Mixin class providing element finding functionality."""
    
    def find_element(self, by: str, value: str) -> WebElement:
        """Find a single element.
        
        Args:
            by: The locator strategy (e.g., 'id', 'xpath', 'css_selector')
            value: The locator value
            
        Returns:
            The found WebElement
            
        Raises:
            NoSuchElementException: If the element is not found
        """
        return self.driver.find_element(by, value)
    
    def find_elements(self, by: str, value: str) -> List[WebElement]:
        """Find multiple elements.
        
        Args:
            by: The locator strategy (e.g., 'id', 'xpath', 'css_selector')
            value: The locator value
            
        Returns:
            List of found WebElements (may be empty)
        """
        return self.driver.find_elements(by, value)
    
    def find_element_by_id(self, id_: str) -> WebElement:
        """Find an element by ID.
        
        Args:
            id_: The ID of the element to find
            
        Returns:
            The found WebElement
            
        Raises:
            NoSuchElementException: If the element is not found
        """
        return self.find_element(By.ID, id_)
    
    def find_elements_by_class_name(self, name: str) -> List[WebElement]:
        """Find elements by class name.
        
        Args:
            name: The class name to find elements by
            
        Returns:
            List of found WebElements (may be empty)
        """
        return self.find_elements(By.CLASS_NAME, name)
    
    def find_element_by_css_selector(self, css_selector: str) -> WebElement:
        """Find an element by CSS selector.
        
        Args:
            css_selector: The CSS selector to find the element
            
        Returns:
            The found WebElement
            
        Raises:
            NoSuchElementException: If the element is not found
        """
        return self.find_element(By.CSS_SELECTOR, css_selector)
    
    def find_elements_by_css_selector(self, css_selector: str) -> List[WebElement]:
        """Find elements by CSS selector.
        
        Args:
            css_selector: The CSS selector to find elements by
            
        Returns:
            List of found WebElements (may be empty)
        """
        return self.find_elements(By.CSS_SELECTOR, css_selector)
    
    def find_element_by_xpath(self, xpath: str) -> WebElement:
        """Find an element by XPath.
        
        Args:
            xpath: The XPath to find the element
            
        Returns:
            The found WebElement
            
        Raises:
            NoSuchElementException: If the element is not found
        """
        return self.find_element(By.XPATH, xpath)
    
    def find_elements_by_xpath(self, xpath: str) -> List[WebElement]:
        """Find elements by XPath.
        
        Args:
            xpath: The XPath to find elements by
            
        Returns:
            List of found WebElements (may be empty)
        """
        return self.find_elements(By.XPATH, xpath)
