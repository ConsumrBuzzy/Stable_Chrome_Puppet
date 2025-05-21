"""Tests for element interaction functionality."""
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.browser.exceptions import (
    ElementNotFoundError,
    ElementNotInteractableError,
    TimeoutError
)

class TestElementInteraction:
    """Test cases for element interaction methods."""
    
    def test_find_element(self, browser, test_page_with_form):
        """Test finding an element by various selectors."""
        browser.get(test_page_with_form)
        
        # Test different selector types
        elements = [
            ("id", "search-input"),
            ("name", "search"),
            ("css", "input[type='text']"),
            ("xpath", "//input[@id='search-input']"),
            ("link text", "Click me"),
            ("partial link text", "Click")
        ]
        
        for by, value in elements:
            element = browser.element.find_element(by, value)
            assert element is not None
            assert element.is_displayed()
    
    def test_find_elements(self, browser, test_page_with_form):
        """Test finding multiple elements."""
        browser.get(test_page_with_form)
        
        # Find all input elements
        inputs = browser.element.find_elements("tag name", "input")
        assert len(inputs) >= 2  # Should find at least search and submit inputs
        
        # Verify all found elements are input elements
        for input_elem in inputs:
            assert input_elem.tag_name.lower() == "input"
    
    def test_element_not_found(self, browser, test_page_with_form):
        """Test handling of non-existent elements."""
        browser.get(test_page_with_form)
        
        with pytest.raises(ElementNotFoundError):
            browser.element.find_element("id", "non-existent-id")
    
    def test_send_keys(self, browser, test_page_with_form):
        """Test sending keys to an input element."""
        browser.get(test_page_with_form)
        
        # Find the search input and type text
        search_input = browser.element.find_element("id", "search-input")
        browser.element.send_keys("test search", element=search_input)
        
        # Verify the text was entered
        assert search_input.get_attribute("value") == "test search"
    
    def test_click(self, browser, test_page_with_form):
        """Test clicking an element."""
        browser.get(test_page_with_form)
        
        # Find and click the submit button
        submit_button = browser.element.find_element("css", "button[type='submit']")
        browser.element.click(submit_button)
        
        # Verify the form was submitted (assuming it navigates to a new page)
        assert "form-submitted" in browser.get_current_url()
    
    def test_get_text(self, browser, test_page_with_form):
        """Test getting text from an element."""
        browser.get(test_page_with_form)
        
        # Get text from a heading
        heading = browser.element.find_element("tag name", "h1")
        text = browser.element.get_text(heading)
        
        assert "Test Form" in text
    
    def test_get_attribute(self, browser, test_page_with_form):
        """Test getting an attribute from an element."""
        browser.get(test_page_with_form)
        
        # Get the type attribute of the search input
        search_input = browser.element.find_element("id", "search-input")
        input_type = browser.element.get_attribute(search_input, "type")
        
        assert input_type == "text"
    
    def test_is_displayed(self, browser, test_page_with_form):
        """Test checking if an element is displayed."""
        browser.get(test_page_with_form)
        
        # Check visible element
        heading = browser.element.find_element("tag name", "h1")
        assert browser.element.is_displayed(heading) is True
        
        # Check hidden element (if exists on the page)
        try:
            hidden_element = browser.element.find_element("id", "hidden-element")
            assert browser.element.is_displayed(hidden_element) is False
        except ElementNotFoundError:
            pytest.skip("No hidden element found on test page")
    
    def test_wait_for_element(self, browser, test_page_with_form):
        """Test waiting for an element to be present."""
        browser.get(test_page_with_form)
        
        # Test waiting for an element that loads immediately
        element = browser.element.wait_for_element("id", "search-input", timeout=5)
        assert element is not None
        
        # Test waiting for an element that appears after a delay
        # (assuming the test page has such an element)
        try:
            delayed_element = browser.element.wait_for_element("id", "delayed-element", timeout=10)
            assert delayed_element is not None
        except ElementNotFoundError:
            pytest.skip("No delayed element found on test page")
