"""
Utility modules for Chrome Puppet.

This package contains various utility modules used throughout the Chrome Puppet
application, including driver management, logging, and other helper functions.
"""

from .driver_manager import ChromeDriverManager, DriverManager, ensure_chromedriver_available
from .signal_handler import signal_handling, register_cleanup, unregister_cleanup, SignalHandler

__all__ = [
    'ChromeDriverManager',
    'DriverManager',
    'ensure_chromedriver_available',
    'signal_handling',
    'register_cleanup',
    'unregister_cleanup',
    'SignalHandler'
]
