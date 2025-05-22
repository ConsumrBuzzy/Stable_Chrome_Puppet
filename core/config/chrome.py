"""Chrome browser configuration."""
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
from .base import BrowserConfig

class ChromeConfig(BrowserConfig):
    """Chrome-specific browser configuration."""
    
    def __init__(self, **kwargs):
        """Initialize Chrome configuration.
        
        Args:
            **kwargs: Additional configuration options
        """
        # Handle both chrome_arguments and arguments for backward compatibility
        chrome_arguments = kwargs.pop('chrome_arguments', None)
        arguments = kwargs.pop('arguments', [])
        
        # Initialize parent class first with remaining kwargs
        super().__init__(**kwargs)
        
        # Chrome-specific configurations
        self.chrome_binary: Optional[str] = kwargs.get('chrome_binary')
        self.chrome_driver_path: Optional[str] = kwargs.get('chrome_driver_path')
        self.experimental_options: Dict[str, Any] = kwargs.get('experimental_options', {})
        
        # Set arguments, preferring chrome_arguments if both are provided
        self.arguments: List[str] = chrome_arguments if chrome_arguments is not None else arguments
        self.extra_args: List[str] = kwargs.get('extra_args', [])  # For backward compatibility
        
        self.extensions: List[Union[str, Path]] = kwargs.get('extensions', [])
        self.prefs: Dict[str, Any] = kwargs.get('prefs', {})
        self.headless: bool = kwargs.get('headless', False)
        
        # Handle window_size - convert to tuple if it's a list
        window_size = kwargs.get('window_size', (1280, 800))
        if isinstance(window_size, list):
            window_size = tuple(window_size)
        self.window_size: Tuple[int, int] = window_size
        
        self.user_data_dir: Optional[str] = kwargs.get('user_data_dir')
        self.download_dir: Optional[str] = kwargs.get('download_dir')
        self.disable_dev_shm_usage: bool = kwargs.get('disable_dev_shm_usage', True)
        self.no_sandbox: bool = kwargs.get('no_sandbox', True)
        self.disable_gpu: bool = kwargs.get('disable_gpu', False)
        self.disable_extensions: bool = kwargs.get('disable_extensions', False)
        self.incognito: bool = kwargs.get('incognito', False)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dict containing configuration options
        """
        config = super().to_dict()
        config.update({
            'chrome_binary': self.chrome_binary,
            'chrome_driver_path': self.chrome_driver_path,
            'experimental_options': self.experimental_options,
            'arguments': self.arguments,
            'extra_args': self.extra_args,
            'extensions': [str(ext) for ext in self.extensions],
            'prefs': self.prefs,
            'headless': self.headless,
            'window_size': self.window_size,
            'user_data_dir': self.user_data_dir,
            'download_dir': self.download_dir,
            'disable_dev_shm_usage': self.disable_dev_shm_usage,
            'no_sandbox': self.no_sandbox,
            'disable_gpu': self.disable_gpu,
            'disable_extensions': self.disable_extensions,
            'incognito': self.incognito,
        })
        return config
