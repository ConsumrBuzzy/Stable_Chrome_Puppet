"""Configuration classes for browser automation.

This module provides configuration classes for different browser types
and their respective options.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


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
    """
    browser_type: str = 'chrome'
    headless: bool = False
    window_size: Tuple[int, int] = (1366, 768)
    implicit_wait: int = 10
    page_load_timeout: int = 30
    script_timeout: int = 30
    extra_args: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {
            'browser_type': self.browser_type,
            'headless': self.headless,
            'window_size': self.window_size,
            'implicit_wait': self.implicit_wait,
            'page_load_timeout': self.page_load_timeout,
            'script_timeout': self.script_timeout,
            'extra_args': self.extra_args
        }


@dataclass
class ChromeConfig(BrowserConfig):
    """Chrome-specific browser configuration."""
    browser_type: str = 'chrome'
    chrome_args: List[str] = field(default_factory=list)
    experimental_options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization setup."""
        if self.headless:
            self.chrome_args.append('--headless=new')
        
        if self.window_size:
            self.chrome_args.append(f'--window-size={self.window_size[0]},{self.window_size[1]}')


# For backward compatibility
BrowserConfig = ChromeConfig
