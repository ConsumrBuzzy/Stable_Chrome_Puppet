"""
Browser configuration system.

This package provides configuration classes for different browser types
and their respective options.
"""

from .base import (
    BaseConfig,
    BrowserConfig,
    BrowserType,
    DriverConfig,
    LogLevel,
    PerformanceLoggingConfig,
    ProfileConfig,
    ProxyConfig,
)
from .chrome import ChromeConfig

__all__ = [
    'BaseConfig',
    'BrowserConfig',
    'BrowserType',
    'ChromeConfig',
    'DriverConfig',
    'LogLevel',
    'PerformanceLoggingConfig',
    'ProfileConfig',
    'ProxyConfig',
]
