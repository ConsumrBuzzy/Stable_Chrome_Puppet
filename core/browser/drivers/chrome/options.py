"""Chrome options configuration.

This module provides a class for configuring Chrome browser options in a type-safe way.
"""
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
from selenium.webdriver.chrome.options import Options as ChromeOptions

from ....types import BrowserConfig, WindowSize


class ChromeOptionsBuilder:
    """Builder for Chrome browser options."""
    
    def __init__(self, config: Optional[BrowserConfig] = None) -> None:
        """Initialize the options builder.
        
        Args:
            config: Browser configuration to use as base.
        """
        self._options = ChromeOptions()
        self._experimental_options: Dict[str, Any] = {}
        self._arguments: List[str] = []
        self._extensions: List[str] = []
        self._window_size: Optional[WindowSize] = None
        self._headless: bool = False
        self._user_agent: Optional[str] = None
        
        if config:
            self.from_config(config)
    
    def from_config(self, config: BrowserConfig) -> 'ChromeOptionsBuilder':
        """Configure options from a BrowserConfig object.
        
        Args:
            config: Browser configuration to use.
            
        Returns:
            Self for method chaining.
        """
        if config.headless:
            self.set_headless()
            
        if config.window_size:
            self.set_window_size(config.window_size)
            
        if config.user_agent:
            self.set_user_agent(config.user_agent)
            
        if config.extra_args:
            self.add_arguments(*config.extra_args)
            
        if config.experimental_options:
            for key, value in config.experimental_options.items():
                self.set_experimental_option(key, value)
                
        return self
    
    def set_headless(self, headless: bool = True) -> 'ChromeOptionsBuilder':
        """Enable or disable headless mode.
        
        Args:
            headless: Whether to enable headless mode.
            
        Returns:
            Self for method chaining.
        """
        self._headless = headless
        if headless:
            self._arguments.append("--headless=new")
        return self
    
    def set_window_size(self, window_size: Union[Tuple[int, int], 'WindowSize', None], 
                       height: Optional[int] = None) -> 'ChromeOptionsBuilder':
        """Set the browser window size.
        
        Args:
            window_size: Either a tuple of (width, height) or a WindowSize named tuple.
            height: Optional height in pixels if window_size is an integer width.
            
        Returns:
            Self for method chaining.
            
        Raises:
            TypeError: If window_size is not a valid type.
        """
        if window_size is None:
            return self
            
        if isinstance(window_size, (tuple, WindowSize)):
            if len(window_size) != 2:
                raise ValueError("Window size must be a tuple of (width, height)")
            width, height = window_size
        elif isinstance(window_size, int) and height is not None:
            width = window_size
        else:
            raise TypeError("Invalid type for window_size. Expected tuple, WindowSize, or int with height")
            
        self._window_size = WindowSize(width, height)
        self._arguments.append(f"--window-size={width},{height}")
        return self
    
    def set_user_agent(self, user_agent: str) -> 'ChromeOptionsBuilder':
        """Set the user agent string.
        
        Args:
            user_agent: User agent string to use.
            
        Returns:
            Self for method chaining.
        """
        self._user_agent = user_agent
        self._arguments.append(f"--user-agent={user_agent}")
        return self
    
    def add_arguments(self, *args: str) -> 'ChromeOptionsBuilder':
        """Add command-line arguments.
        
        Args:
            *args: Arguments to add.
            
        Returns:
            Self for method chaining.
        """
        self._arguments.extend(args)
        return self
    
    def add_extension(self, extension_path: Union[str, Path]) -> 'ChromeOptionsBuilder':
        """Add a Chrome extension.
        
        Args:
            extension_path: Path to the extension (.crx file).
            
        Returns:
            Self for method chaining.
        """
        self._extensions.append(str(extension_path))
        return self
    
    def set_experimental_option(self, name: str, value: Any) -> 'ChromeOptionsBuilder':
        """Set an experimental option.
        
        Args:
            name: Option name.
            value: Option value.
            
        Returns:
            Self for method chaining.
        """
        self._experimental_options[name] = value
        return self
    
    def build(self) -> ChromeOptions:
        """Build the Chrome options.
        
        Returns:
            Configured ChromeOptions instance.
        """
        options = ChromeOptions()
        
        # Add all arguments
        for arg in set(self._arguments):  # Use set to remove duplicates
            options.add_argument(arg)
            
        # Add extensions
        for ext in self._extensions:
            options.add_extension(ext)
            
        # Add experimental options
        for key, value in self._experimental_options.items():
            options.set_experimental_option(key, value)
            
        return options
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert options to a dictionary.
        
        Returns:
            Dictionary representation of the options.
        """
        return {
            'headless': self._headless,
            'window_size': (self._window_size.width, self._window_size.height) if self._window_size else None,
            'user_agent': self._user_agent,
            'arguments': self._arguments,
            'extensions': self._extensions,
            'experimental_options': self._experimental_options
        }
