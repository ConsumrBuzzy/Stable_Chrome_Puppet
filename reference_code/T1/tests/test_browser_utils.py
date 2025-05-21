import unittest
from unittest.mock import patch, MagicMock
from utils import browser_utils

class TestBrowserUtils(unittest.TestCase):
    def test_is_chromedriver_compatible_always_true(self):
        # This function is currently a stub that always returns True
        self.assertTrue(browser_utils.is_chromedriver_compatible('any_path'))

    def test_create_driver_fallback(self):
        # Patch ChromeDriverManager to avoid actual downloads
        with patch('utils.browser_utils.ChromeDriverManager') as mock_mgr, \
             patch('utils.browser_utils.webdriver.Chrome') as mock_chrome:
            mock_mgr.return_value.install.return_value = 'fake_path'
            mock_driver = MagicMock()
            mock_chrome.return_value = mock_driver
            driver = browser_utils.create_driver()
            self.assertEqual(driver, mock_driver)

if __name__ == '__main__':
    unittest.main()
