"""
Core functionality for Chrome Puppet.

This module provides the main browser automation capabilities for Chrome Puppet.
"""

# Lazy imports to prevent circular dependencies
ChromeDriver = None
ChromeConfig = None
DEFAULT_CONFIG = None

def _import_chrome_driver():
    """Lazy import for ChromeDriver to avoid circular imports."""
    global ChromeDriver
    if ChromeDriver is None:
        from .browser.drivers.chrome_driver import ChromeDriver as CD
        ChromeDriver = CD
    return ChromeDriver

def _import_config():
    """Lazy import for ChromeConfig to avoid circular imports."""
    global ChromeConfig, DEFAULT_CONFIG
    if ChromeConfig is None or DEFAULT_CONFIG is None:
        from .browser.config import ChromeConfig as CC, DEFAULT_CONFIG as DC
        ChromeConfig = CC
        DEFAULT_CONFIG = DC
    return ChromeConfig, DEFAULT_CONFIG

# Set default logging configuration
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

__all__ = [
    'ChromeDriver',
    'ChromeConfig',
    'DEFAULT_CONFIG',
    '_import_chrome_driver',
    '_import_config'
]
