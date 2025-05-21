import unittest
from unittest.mock import patch, MagicMock
import core.zoom_login as zoom_login_mod

class TestZoomLogin(unittest.TestCase):
    @patch('core.zoom_login.wait_and_fill')
    @patch('core.zoom_login.wait_and_click')
    @patch('core.zoom_login.wait_for_element_or_url')
    def test_zoom_login_success(self, mock_wait_for_element_or_url, mock_wait_and_click, mock_wait_and_fill):
        driver = MagicMock()
        # Simulate user already on dashboard/profile
        mock_wait_for_element_or_url.return_value = 'url'
        result = zoom_login_mod.zoom_login(driver, 'test@example.com', 'pw', max_retries=1)
        self.assertTrue(result)

    @patch('core.zoom_login.log_and_screenshot')
    @patch('core.zoom_login.wait_and_fill')
    @patch('core.zoom_login.wait_and_click')
    @patch('core.zoom_login.wait_for_element_or_url')
    def test_zoom_login_failure(self, mock_wait_for_element_or_url, mock_wait_and_click, mock_wait_and_fill, mock_log_and_screenshot):
        driver = MagicMock()
        # Simulate always failing to reach dashboard/profile
        mock_wait_for_element_or_url.return_value = 'element'
        mock_wait_and_fill.return_value = None
        mock_wait_and_click.side_effect = Exception('No button')
        # Should raise after retries
        with self.assertRaises(Exception):
            zoom_login_mod.zoom_login(driver, 'test@example.com', 'pw', max_retries=1)
        mock_log_and_screenshot.assert_called()

if __name__ == '__main__':
    unittest.main()
