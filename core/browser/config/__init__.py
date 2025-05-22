"""
Browser configuration system.

This package provides configuration classes for different browser types
and their respective options.
"""

from .base import BrowserConfig, ProfileConfig

# ChromeConfig is now in core.browser.drivers.chrome.config
__all__ = ['BrowserConfig', 'ProfileConfig']
