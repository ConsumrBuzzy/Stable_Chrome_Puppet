"""Test browser initialization and basic functionality."""
import os
import sys
import unittest
import time
from pathlib import Path

# Add parent directory to path to import our package
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from selenium.webdriver.common.by import By

# Import base test
if __name__ == '__main__':
    # When running this file directly
    from base_test import BaseTest
else:
    # When running as part of a test suite
    from tests.base_test import BaseTest

class TestBrowserInitialization(BaseTest):
    """Test browser initialization and basic operations."""
    
    def test_browser_initialization(self):
        """Test that the browser initializes correctly."""
        with self.create_browser() as browser:
            # Check that the browser is created
            self.assertIsNotNone(browser.driver)
            self.assertIsNotNone(browser.driver.capabilities)
            
            # Check that we can navigate to a page
            browser.get("https://httpbin.org/headers")
            self.assertIn("httpbin.org", browser.driver.current_url)
            
            # Take a screenshot for verification
            self.take_screenshot(browser, "browser_init_test")
            
            # Check page title
            self.assertIn("httpbin.org", browser.driver.title)
    
    def test_javascript_execution(self):
        """Test JavaScript execution in the browser."""
        with self.create_browser() as browser:
            # Execute JavaScript
            user_agent = browser.driver.execute_script("return navigator.userAgent;")
            self.assertIsInstance(user_agent, str)
            self.assertIn("Chrome", user_agent)
            
            # Test console.log capture
            browser.driver.execute_script("console.log('Test message from JavaScript');")
    
    def test_window_management(self):
        """Test browser window management."""
        config = {
            'window_size': (1024, 768),
            'headless': False  # Need visible window for size tests
        }
        
        with self.create_browser(config) as browser:
            # Test window size
            size = browser.driver.get_window_size()
            self.assertEqual(size['width'], 1024)
            self.assertEqual(size['height'], 768)
            
            # Test window position
            browser.driver.set_window_position(100, 200)
            position = browser.driver.get_window_position()
            self.assertEqual(position['x'], 100)
            self.assertEqual(position['y'], 200)

if __name__ == "__main__":
    TestBrowserInitialization.main()
