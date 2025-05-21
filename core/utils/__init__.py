"""
Utility functions and helpers for Chrome Puppet.

This package contains various utility modules that provide helper functions
and classes used throughout the application, including driver management,
logging, and other helper functions.
"""

from .driver_manager import ChromeDriverManager, DriverManager, ensure_chromedriver_available
from .signal_handler import signal_handling, register_cleanup, unregister_cleanup, SignalHandler
from .retry import retry_on_exception, retry_with_timeout

__all__ = [
    'ChromeDriverManager',
    'DriverManager',
    'ensure_chromedriver_available',
    'signal_handling',
    'register_cleanup',
    'unregister_cleanup',
    'SignalHandler',
    'retry_on_exception',
    'retry_with_timeout'
]
