import unittest
from utils import exceptions

class TestCustomExceptions(unittest.TestCase):
    def test_zoom_login_failed_exception(self):
        e = exceptions.ZoomLoginFailedException('fail')
        self.assertIsInstance(e, exceptions.ZoomLoginFailedException)
        self.assertTrue(issubclass(type(e), Exception))

    def test_captcha_detected_exception(self):
        e = exceptions.CaptchaDetectedException('captcha')
        self.assertIsInstance(e, exceptions.CaptchaDetectedException)
        self.assertTrue(issubclass(type(e), Exception))

    def test_element_not_found_exception(self):
        e = exceptions.ElementNotFoundException('not found')
        self.assertIsInstance(e, exceptions.ElementNotFoundException)
        self.assertTrue(issubclass(type(e), Exception))

if __name__ == '__main__':
    unittest.main()
