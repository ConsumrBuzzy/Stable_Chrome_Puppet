"""Test package for Chrome Puppet."""

# Import test utilities and base classes
from .base_test import BaseTest
from .test_browser_init import TestBrowserInitialization
from .test_navigation import TestNavigation
from .test_screenshot import TestScreenshot

__all__ = [
    'BaseTest',
    'TestBrowserInitialization',
    'TestNavigation',
    'TestScreenshot'
]
