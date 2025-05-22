"""
Test package for Chrome Puppet.

This package contains all the test cases and utilities for testing Chrome Puppet.
"""

# Import test utilities and base classes
from .test_browser import TestChromeDriver as TestBrowser
from .test_chrome_driver import TestChromeDriver

# Make test cases available at package level
__all__ = [
    'TestBrowser',  # Alias for TestChromeDriver from test_browser
    'TestChromeDriver',
]

# Configure test logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
