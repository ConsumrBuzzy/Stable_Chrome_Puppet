"""Test screenshot capture functionality."""
import unittest
import os
from pathlib import Path

from selenium.webdriver.common.by import By

from .base_test import BaseTest

class TestScreenshot(BaseTest):
    """Test screenshot capture functionality."""
    
    def test_full_page_screenshot(self):
        """Test capturing a full page screenshot."""
        with self.create_browser() as browser:
            # Navigate to a test page
            browser.get("https://httpbin.org/html")
            
            # Take a full page screenshot
            screenshot_path = self.take_screenshot(browser, "full_page")
            
            # Verify the screenshot was created
            self.assertTrue(Path(screenshot_path).exists())
            self.assertGreater(os.path.getsize(screenshot_path), 0)
    
    def test_element_screenshot(self):
        """Test capturing a screenshot of a specific element."""
        with self.create_browser() as browser:
            # Navigate to a test page with distinct elements
            browser.get("https://httpbin.org/html")
            
            # Find an element to capture
            element = self.assertElementPresent(
                browser, By.CSS_SELECTOR, "div.ng-scope"
            )
            
            # Take element screenshot
            element_screenshot = element.screenshot_as_png
            
            # Save the element screenshot
            screenshots_dir = Path('screenshots')
            screenshots_dir.mkdir(exist_ok=True)
            element_path = screenshots_dir / "element_screenshot.png"
            
            with open(element_path, 'wb') as f:
                f.write(element_screenshot)
            
            # Verify the screenshot was created
            self.assertTrue(element_path.exists())
            self.assertGreater(element_path.stat().st_size, 0)
    
    def test_viewport_screenshot(self):
        """Test capturing the current viewport screenshot."""
        with self.create_browser() as browser:
            # Navigate to a test page
            browser.get("https://httpbin.org/")
            
            # Take viewport screenshot
            screenshot_path = self.take_screenshot(browser, "viewport")
            
            # Verify the screenshot was created
            self.assertTrue(Path(screenshot_path).exists())
            self.assertGreater(os.path.getsize(screenshot_path), 0)
            
            # Resize window and take another screenshot
            browser.driver.set_window_size(800, 600)
            resized_path = self.take_screenshot(browser, "resized_viewport")
            
            # Verify the resized screenshot was created
            self.assertTrue(Path(resized_path).exists())
            self.assertGreater(os.path.getsize(resized_path), 0)

if __name__ == "__main__":
    TestScreenshot.main()
