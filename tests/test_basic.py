"""
Basic test cases for Chrome Puppet.

These tests verify the core functionality of the Chrome Puppet browser automation tool.
"""
import os
import sys
import logging
import unittest
from pathlib import Path
from typing import Optional

# Add parent directory to path to allow package imports
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from core.browser.puppet import ChromePuppet
from core.browser.chrome import ChromeConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestChromePuppetBasic(unittest.TestCase):
    """Basic test cases for Chrome Puppet."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Create test directories if they don't exist
        Path("logs").mkdir(exist_ok=True)
        Path("screenshots").mkdir(exist_ok=True)
    
    def setUp(self):
        """Set up test case."""
        self.config = ChromeConfig(
            headless=True,  # Run in headless mode for CI/CD
            window_size=(1366, 768),
            verbose=True
        )
    
    def test_browser_initialization(self):
        """Test that the browser initializes correctly."""
        with ChromePuppet(config=self.config) as browser:
            self.assertIsNotNone(browser.driver, "WebDriver should be initialized")
            self.assertTrue(hasattr(browser, 'driver'), "Browser should have 'driver' attribute")
            logger.info("Browser initialized successfully")
    
    def test_navigation(self):
        """Test basic navigation functionality."""
        test_url = "https://www.example.com"
        with ChromePuppet(config=self.config) as browser:
            browser.get(test_url)
            self.assertIn("Example Domain", browser.driver.title)
            logger.info(f"Successfully navigated to {test_url}")
    
    def test_screenshot(self):
        """Test screenshot functionality."""
        with ChromePuppet(config=self.config) as browser:
            browser.get("https://www.example.com")
            # Generate a unique filename for the screenshot
            import time
            timestamp = int(time.time())
            screenshot_filename = f"test_screenshot_{timestamp}.png"
            screenshot_path = Path("screenshots") / screenshot_filename
            
            # Take the screenshot
            success = browser.take_screenshot(str(screenshot_path))
            self.assertTrue(success, "Screenshot should be taken successfully")
            
            # Verify the file was created
            self.assertTrue(screenshot_path.exists(), f"Screenshot file should exist at {screenshot_path}")
            self.assertGreater(screenshot_path.stat().st_size, 0, "Screenshot file should not be empty")
            logger.info(f"Screenshot saved to {screenshot_path}")
            
            # Clean up after test
            if screenshot_path.exists():
                screenshot_path.unlink()
    
    def test_custom_user_agent(self):
        """Test custom user agent setting."""
        custom_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ChromePuppet/1.0"
        config = ChromeConfig(
            headless=True,
            user_agent=custom_ua
        )
        with ChromePuppet(config=config) as browser:
            browser.get("https://httpbin.org/user-agent")
            # The page returns the user agent in the response body
            user_agent = browser.driver.find_element("tag name", "body").text
            self.assertIn(custom_ua, user_agent)
            logger.info(f"Verified custom user agent: {custom_ua}")

if __name__ == "__main__":
    unittest.main()
