"""Base test class for Chrome Puppet tests."""
import os
import sys
import logging
import unittest
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union

# Add parent directory to path to import our package
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

# Import ChromePuppet and ChromeConfig
from browser import ChromePuppet
from config import ChromeConfig

class BaseTest(unittest.TestCase):
    """Base test class with common setup and teardown."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('test.log')
            ]
        )
        cls.logger = logging.getLogger(cls.__name__)
        
        # Default configuration
        cls.default_config = {
            'headless': True,
            'window_size': (1400, 1000),
            'download_dir': str(Path('downloads').absolute()),
            'chrome_arguments': [
                '--disable-notifications',
                '--disable-infobars',
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        }
    
    def create_browser(self, config: Optional[Dict[str, Any]] = None) -> ChromePuppet:
        """Create a new browser instance with the given configuration.
        
        Args:
            config: Optional configuration overrides
            
        Returns:
            ChromePuppet: Configured browser instance
        """
        # Merge default config with any overrides
        final_config = self.default_config.copy()
        if config:
            final_config.update(config)
        
        # Create and return the browser
        chrome_config = ChromeConfig(**final_config)
        return ChromePuppet(config=chrome_config)
    
    def assertElementPresent(self, browser, by, value, timeout=10):
        """Assert that an element is present on the page.
        
        Args:
            browser: ChromePuppet instance
            by: Selenium locator strategy (e.g., By.ID, By.CLASS_NAME)
            value: Locator value
            timeout: Maximum time to wait in seconds
            
        Returns:
            WebElement: The found element
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        try:
            element = WebDriverWait(browser.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            self.fail(f"Element {by}={value} not found within {timeout} seconds: {e}")
    
    def take_screenshot(self, browser, filename: str) -> str:
        """Take a screenshot and save it to a file.
        
        Args:
            browser: ChromePuppet instance
            filename: Name of the file to save (without extension)
            
        Returns:
            str: Path to the saved screenshot
        """
        screenshots_dir = Path('screenshots')
        screenshots_dir.mkdir(exist_ok=True)
        
        filepath = screenshots_dir / f"{filename}.png"
        browser.driver.save_screenshot(str(filepath))
        self.logger.info(f"Screenshot saved to {filepath}")
        return str(filepath)
    
    @classmethod
    def parse_args(cls):
        """Parse command line arguments for tests."""
        parser = argparse.ArgumentParser(description='Run Chrome Puppet tests')
        parser.add_argument('--headless', action='store_true', help='Run in headless mode')
        parser.add_argument('--debug', action='store_true', help='Enable debug logging')
        return parser.parse_args()
    
    @classmethod
    def main(cls):
        """Run the test case with command line arguments."""
        args = cls.parse_args()
        
        # Update default config based on args
        if args.headless:
            cls.default_config['headless'] = True
        
        # Run the tests
        unittest.main(argv=sys.argv[:1])
