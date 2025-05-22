"""
Browser configuration system.

This package provides configuration classes for different browser types
and their respective options.
"""

from .base import BrowserConfig, ProfileConfig
from .chrome import ChromeConfig

__all__ = ['BrowserConfig', 'ProfileConfig', 'ChromeConfig']
