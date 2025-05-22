""
Base configuration classes for browser automation.

This module provides the base configuration classes that are extended
by browser-specific configurations.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class DriverConfig:
    """Configuration for browser drivers.
    
    Attributes:
        driver_path: Path to the WebDriver executable
        service_args: Additional arguments to pass to the WebDriver service
        service_log_path: Path to the WebDriver service log file
    """
    driver_path: Optional[str] = None
    service_args: List[str] = field(default_factory=list)
    service_log_path: Optional[str] = None


@dataclass
class ProfileConfig:
    """Configuration for browser profiles.
    
    Attributes:
        name: Name of the profile
        path: Path to the profile directory
        is_temporary: Whether this is a temporary profile
        preferences: Browser-specific profile preferences
        extensions: List of extension paths to install
    """
    name: str = 'default'
    path: Optional[Union[str, Path]] = None
    is_temporary: bool = False
    preferences: Dict[str, Any] = field(default_factory=dict)
    extensions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {
            'name': self.name,
            'path': str(self.path) if self.path else None,
            'is_temporary': self.is_temporary,
            'preferences': self.preferences,
            'extensions': self.extensions
        }


@dataclass
class BrowserConfig:
    """Base configuration for browser instances.
    
    Attributes:
        browser_type: Type of browser to use (e.g., 'chrome', 'firefox')
        headless: Whether to run the browser in headless mode
        window_size: Window size as (width, height) tuple
        implicit_wait: Default implicit wait time in seconds
        page_load_timeout: Page load timeout in seconds
        script_timeout: Script execution timeout in seconds
        extra_args: Additional browser-specific arguments
        driver_config: Configuration for the browser driver
        profile_config: Configuration for the browser profile
    """
    browser_type: str = 'chrome'
    headless: bool = False
    window_size: Tuple[int, int] = (1366, 768)
    implicit_wait: int = 10
    page_load_timeout: int = 30
    script_timeout: int = 30
    extra_args: List[str] = field(default_factory=list)
    driver_config: DriverConfig = field(default_factory=DriverConfig)
    profile_config: ProfileConfig = field(default_factory=ProfileConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {
            'browser_type': self.browser_type,
            'headless': self.headless,
            'window_size': self.window_size,
            'implicit_wait': self.implicit_wait,
            'page_load_timeout': self.page_load_timeout,
            'script_timeout': self.script_timeout,
            'extra_args': self.extra_args,
            'driver_config': {
                'driver_path': self.driver_config.driver_path,
                'service_args': self.driver_config.service_args,
                'service_log_path': self.driver_config.service_log_path
            },
            'profile_config': self.profile_config.to_dict()
        }
