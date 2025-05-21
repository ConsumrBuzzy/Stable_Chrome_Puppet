"""
Core functionality for Chrome Puppet.

This module provides the main browser automation capabilities for Chrome Puppet.
"""

from .browser.chrome import ChromeBrowser
from .config import ChromeConfig, DEFAULT_CONFIG

__all__ = [
    'ChromeBrowser',
    'ChromeConfig',
    'DEFAULT_CONFIG',
]

# Set default logging configuration
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
