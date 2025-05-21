import unittest
from unittest.mock import patch
from utils import system_utils

class TestSystemUtils(unittest.TestCase):
    def test_get_python_bitness_returns_32_or_64(self):
        bitness = system_utils.get_python_bitness()
        self.assertIn(bitness, ['32', '64'])

    def test_check_architecture_runs_without_exception(self):
        # Should not raise, regardless of system architecture
        try:
            system_utils.check_architecture()
        except Exception as e:
            self.fail(f"check_architecture() raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()
