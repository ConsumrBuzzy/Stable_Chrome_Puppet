"""
Test package for Chrome Puppet.

This package contains all the test cases and utilities for testing Chrome Puppet.
"""

# Import test classes with lazy loading to prevent circular imports
TestBrowser = None
TestChromeDriver = None

def _import_test_classes():
    """Lazy import test classes to prevent circular imports."""
    global TestBrowser, TestChromeDriver
    
    if TestBrowser is None:
        from .test_browser import TestChromeDriver as TB
        TestBrowser = TB
    
    if TestChromeDriver is None:
        from .test_chrome_driver import TestChromeDriver as TCD
        TestChromeDriver = TCD
    
    return TestBrowser, TestChromeDriver

# Expose the test classes in __all__
__all__ = ['TestBrowser', 'TestChromeDriver']

# Configure test logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
