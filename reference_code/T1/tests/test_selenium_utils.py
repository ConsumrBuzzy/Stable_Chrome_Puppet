import unittest
from unittest.mock import MagicMock
from utils import selenium_utils

class TestSeleniumUtils(unittest.TestCase):
    def setUp(self):
        # Create a mock driver and element for all tests
        self.driver = MagicMock()
        self.mock_elem = MagicMock()

    def test_wait_and_fill_calls_clear_and_send_keys(self):
        # Patch wait_for_element to return a mock element
        selenium_utils.wait_for_element = MagicMock(return_value=self.mock_elem)
        selenium_utils.wait_and_fill(self.driver, 'id', 'fake_id', 'test text', timeout=5)
        self.mock_elem.clear.assert_called_once()
        self.mock_elem.send_keys.assert_called_once_with('test text')

    def test_wait_and_click_calls_click(self):
        # Patch wait_for_clickable to return a mock element
        selenium_utils.wait_for_clickable = MagicMock(return_value=self.mock_elem)
        selenium_utils.wait_and_click(self.driver, 'id', 'fake_id', timeout=5)
        self.mock_elem.click.assert_called_once()

    def test_log_and_screenshot_calls_log_error_and_save_screenshot(self):
        # Patch log_error and save_screenshot at their true import locations
        with unittest.mock.patch('utils.logging_utils.log_error') as mock_log_error, \
             unittest.mock.patch('utils.screenshot_utils.save_screenshot') as mock_save_screenshot:
            selenium_utils.log_and_screenshot(self.driver, 'msg', 'prefix')
            mock_log_error.assert_called_once_with('msg')
            mock_save_screenshot.assert_called_once_with(self.driver, 'prefix')

if __name__ == '__main__':
    unittest.main()
