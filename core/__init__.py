"""
Core functionality for Chrome Puppet.

This module provides the main browser automation capabilities for Chrome Puppet.
"""

from .browser.drivers.chrome_driver import ChromeDriver
from .browser.config import ChromeConfig, DEFAULT_CONFIG

__all__ = [
    'ChromeDriver',
    'ChromeConfig',
    'DEFAULT_CONFIG',
]

# Set default logging configuration
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
