"""
Test package for Chrome Puppet.

This package contains all the test cases and utilities for testing Chrome Puppet.
"""

# Import test utilities and base classes
from .base_test import BaseTest
from .test_browser_init import TestBrowserInitialization
from .test_navigation import TestNavigation
from .test_screenshot import TestScreenshot

# Make test cases available at package level
__all__ = [
    'BaseTest',
    'TestBrowserInitialization',
    'TestNavigation',
    'TestScreenshot',
]

# Configure test logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
