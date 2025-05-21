"""
Utility modules for Chrome Puppet.

This package contains various utility modules used throughout the Chrome Puppet
application, including driver management, logging, and other helper functions.
"""

from .driver_manager import ChromeDriverManager, ensure_chromedriver_available

__all__ = ['ChromeDriverManager', 'ensure_chromedriver_available']
