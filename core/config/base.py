"""
Base configuration classes for browser automation.

This module provides the base configuration classes that are extended
by browser-specific configurations.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, TypeVar, Generic, Type, ClassVar

# Import from the new location
from ..exceptions import BrowserError

# Type variable for configuration classes
T = TypeVar('T', bound='BaseConfig')


class BrowserType(str, Enum):
    """Supported browser types."""
    CHROME = 'chrome'
    FIREFOX = 'firefox'
    EDGE = 'edge'
    SAFARI = 'safari'
    OPERA = 'opera'
    BRAVE = 'brave'


class LogLevel(str, Enum):
    """Logging levels for browser and driver."""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    OFF = 'OFF'


@dataclass
class BaseConfig:
    """Base configuration class with common functionality."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create a configuration instance from a dictionary."""
        return cls(**data)  # type: ignore


@dataclass
class DriverConfig(BaseConfig):
    """Configuration for browser drivers.
    
    Attributes:
        driver_path: Path to the WebDriver executable.
        service_args: Additional arguments to pass to the WebDriver service.
        service_log_path: Path to the WebDriver service log file.
        log_level: Logging level for the WebDriver service.
        host: Host address for the WebDriver service.
        port: Port number for the WebDriver service.
        env: Environment variables to pass to the WebDriver service.
    """
    driver_path: Optional[Union[str, Path]] = None
    service_args: List[str] = field(default_factory=list)
    service_log_path: Optional[Union[str, Path]] = None
    log_level: LogLevel = LogLevel.INFO
    host: str = '127.0.0.1'
    port: int = 0  # 0 means use any free port
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProxyConfig(BaseConfig):
    """Configuration for proxy settings.
    
    Attributes:
        http_proxy: HTTP proxy URL (e.g., 'http://proxy:port').
        https_proxy: HTTPS proxy URL (e.g., 'https://proxy:port').
        no_proxy: List of hosts that should bypass the proxy.
        proxy_type: Type of proxy (e.g., 'manual', 'pac', 'autodetect', 'system').
        proxy_autoconfig_url: URL for proxy auto-configuration (PAC) file.
        ssl_proxy: SSL proxy settings.
        socks_proxy: SOCKS proxy settings.
        socks_version: SOCKS version (4 or 5).
        proxy_bypass: List of hosts to bypass proxy for.
    """
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    no_proxy: List[str] = field(default_factory=list)
    proxy_type: str = 'manual'
    proxy_autoconfig_url: Optional[str] = None
    ssl_proxy: Optional[str] = None
    socks_proxy: Optional[str] = None
    socks_version: Optional[int] = None
    proxy_bypass: List[str] = field(default_factory=list)


@dataclass
class ProfileConfig(BaseConfig):
    """Configuration for browser profiles.
    
    Attributes:
        name: Name of the profile.
        path: Path to the profile directory.
        is_temporary: Whether this is a temporary profile.
        preferences: Browser-specific profile preferences.
        extensions: List of extension paths to install.
        accept_insecure_certs: Whether to accept insecure certificates.
        default_content_setting_values: Default content settings.
        password_manager_enabled: Whether password manager is enabled.
    """
    name: str = 'default'
    path: Optional[Union[str, Path]] = None
    is_temporary: bool = False
    preferences: Dict[str, Any] = field(default_factory=dict)
    extensions: List[Union[str, Path]] = field(default_factory=list)
    accept_insecure_certs: bool = False
    default_content_setting_values: Dict[str, Any] = field(default_factory=dict)
    password_manager_enabled: bool = True


@dataclass
class PerformanceLoggingConfig(BaseConfig):
    """Configuration for performance logging.
    
    Attributes:
        enable_performance_logging: Whether to enable performance logging.
        enable_page_load_strategy: Whether to enable page load strategy.
        performance_logging_prefs: Performance logging preferences.
    """
    enable_performance_logging: bool = False
    enable_page_load_strategy: bool = True
    performance_logging_prefs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BrowserConfig(BaseConfig):
    """Base configuration for browser instances.
    
    Attributes:
        browser_type: Type of browser to use (e.g., 'chrome', 'firefox').
        headless: Whether to run the browser in headless mode.
        window_size: Window size as (width, height) tuple.
        window_position: Window position as (x, y) tuple.
        implicit_wait: Default implicit wait time in seconds.
        page_load_timeout: Page load timeout in seconds.
        script_timeout: Script execution timeout in seconds.
        extra_args: Additional browser-specific arguments.
        experimental_options: Experimental browser options.
        driver_config: Configuration for the browser driver.
        profile_config: Configuration for the browser profile.
        proxy_config: Configuration for proxy settings.
        performance_config: Configuration for performance logging.
        logging_prefs: Logging preferences.
        download_dir: Default download directory.
    """
    browser_type: BrowserType = BrowserType.CHROME
    headless: bool = False
    window_size: Tuple[int, int] = (1366, 768)
    window_position: Tuple[int, int] = (0, 0)
    implicit_wait: float = 10.0
    page_load_timeout: float = 30.0
    script_timeout: float = 30.0
    extra_args: List[str] = field(default_factory=list)
    experimental_options: Dict[str, Any] = field(default_factory=dict)
    driver_config: DriverConfig = field(default_factory=DriverConfig)
    profile_config: ProfileConfig = field(default_factory=ProfileConfig)
    proxy_config: Optional[ProxyConfig] = None
    performance_config: PerformanceLoggingConfig = field(default_factory=PerformanceLoggingConfig)
    logging_prefs: Dict[str, str] = field(default_factory=dict)
    download_dir: Optional[Union[str, Path]] = None
    
    def __post_init__(self) -> None:
        """Post-initialization validation."""
        if not isinstance(self.browser_type, BrowserType):
            self.browser_type = BrowserType(self.browser_type.lower())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        data = super().to_dict()
        # Convert enums to strings
        if 'browser_type' in data and data['browser_type'] is not None:
            data['browser_type'] = data['browser_type'].value
        if 'log_level' in data.get('driver_config', {}) and data['driver_config']['log_level'] is not None:
            data['driver_config']['log_level'] = data['driver_config']['log_level'].value
        return data
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create a configuration instance from a dictionary."""
        # Handle nested config objects
        if 'driver_config' in data and isinstance(data['driver_config'], dict):
            data['driver_config'] = DriverConfig.from_dict(data['driver_config'])
        if 'profile_config' in data and isinstance(data['profile_config'], dict):
            data['profile_config'] = ProfileConfig.from_dict(data['profile_config'])
        if 'proxy_config' in data and isinstance(data['proxy_config'], dict):
            data['proxy_config'] = ProxyConfig.from_dict(data['proxy_config'])
        if 'performance_config' in data and isinstance(data['performance_config'], dict):
            data['performance_config'] = PerformanceLoggingConfig.from_dict(data['performance_config'])
        return super().from_dict(data)
