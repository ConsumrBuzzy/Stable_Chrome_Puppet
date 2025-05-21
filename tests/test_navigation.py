"""Test browser navigation and page interactions."""
import os
import sys
import unittest
import time
from pathlib import Path

# Add parent directory to path to import our package
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Import base test
from tests.base_test import BaseTest

class TestNavigation(BaseTest):
    """Test browser navigation and page interactions."""
    
    def test_basic_navigation(self):
        """Test basic navigation between pages."""
        with self.create_browser() as browser:
            # Test navigation to a page
            test_url = "https://httpbin.org/headers"
            browser.get(test_url)
            self.assertEqual(browser.driver.current_url, test_url)
            
            # Test page title
            self.assertIn("httpbin.org", browser.driver.title)
            
            # Test page source
            page_source = browser.driver.page_source
            self.assertIn("httpbin.org", page_source)
    
    def test_element_interaction(self):
        """Test interacting with page elements."""
        with self.create_browser() as browser:
            # Navigate to a test page with forms
            browser.get("https://httpbin.org/forms/post")
            
            # Find and interact with form elements
            customer_name = self.assertElementPresent(
                browser, By.NAME, "custname"
            )
            customer_name.send_keys("Test User")
            
            # Check radio button
            size_medium = self.assertElementPresent(
                browser, By.CSS_SELECTOR, "input[value='medium']"
            )
            size_medium.click()
            
            # Check checkbox
            bacon = self.assertElementPresent(
                browser, By.CSS_SELECTOR, "input[value='bacon']"
            )
            if not bacon.is_selected():
                bacon.click()
            
            # Take a screenshot of the filled form
            self.take_screenshot(browser, "filled_form")
            
            # Verify values
            self.assertEqual(customer_name.get_attribute("value"), "Test User")
            self.assertTrue(size_medium.is_selected())
            self.assertTrue(bacon.is_selected())
    
    def test_wait_for_elements(self):
        """Test waiting for elements to appear."""
        with self.create_browser() as browser:
            # Navigate to a page with dynamic content
            browser.get("https://httpbin.org/delay/2")
            
            # Wait for specific content to appear
            try:
                WebDriverWait(browser.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "html"))
                )
                self.take_screenshot(browser, "delayed_page_loaded")
            except Exception as e:
                self.fail(f"Failed to wait for element: {e}")

if __name__ == "__main__":
    TestNavigation.main()
