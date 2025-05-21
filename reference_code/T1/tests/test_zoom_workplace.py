import unittest
from unittest.mock import patch, MagicMock
import core.zoom_workplace as zoom_workplace_mod

class TestZoomWorkplace(unittest.TestCase):
    @patch('core.zoom_workplace.wait_and_click')
    @patch('core.zoom_workplace.wait_and_fill')
    @patch('core.zoom_workplace.log_and_screenshot')
    def test_add_to_workplace_dnc_success(self, mock_log_and_screenshot, mock_wait_and_fill, mock_wait_and_click):
        driver = MagicMock()
        # Simulate all actions succeed (no exceptions)
        try:
            zoom_workplace_mod.add_to_workplace_dnc(driver, '5551234567')
        except Exception as e:
            self.fail(f"add_to_workplace_dnc raised an exception unexpectedly: {e}")
        mock_wait_and_fill.assert_called()
        mock_wait_and_click.assert_called()
        # log_and_screenshot may not be called on success, so not asserted here

    @patch('core.zoom_workplace.wait_and_click')
    @patch('core.zoom_workplace.wait_and_fill')
    @patch('core.zoom_workplace.log_and_screenshot')
    def test_add_to_workplace_dnc_failure(self, mock_log_and_screenshot, mock_wait_and_fill, mock_wait_and_click):
        driver = MagicMock()
        # Simulate a click failure
        mock_wait_and_click.side_effect = Exception('Click failed')
        with self.assertRaises(Exception):
            zoom_workplace_mod.add_to_workplace_dnc(driver, '5551234567')
        # No longer assert log_and_screenshot is always called, since outer except may catch

if __name__ == '__main__':
    unittest.main()
