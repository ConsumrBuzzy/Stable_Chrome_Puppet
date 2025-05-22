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

__all__ = [
    'BaseConfig',
    'BrowserConfig',
    'BrowserType',
    'DriverConfig',
    'LogLevel',
    'PerformanceLoggingConfig',
    'ProfileConfig',
    'ProxyConfig',
]
