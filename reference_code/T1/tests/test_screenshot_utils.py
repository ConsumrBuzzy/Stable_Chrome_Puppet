import unittest
from unittest.mock import patch, MagicMock
from utils import screenshot_utils

class TestScreenshotUtils(unittest.TestCase):
    def test_save_screenshot_calls_driver_and_logs(self):
        mock_driver = MagicMock()
        with patch.object(screenshot_utils, 'get_logger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            path = screenshot_utils.save_screenshot(mock_driver, 'testprefix')
            mock_driver.save_screenshot.assert_called()
            mock_logger.info.assert_called()
            self.assertTrue(path.endswith('.png'))

if __name__ == '__main__':
    unittest.main()
