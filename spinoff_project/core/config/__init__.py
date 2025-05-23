"""Browser configuration system.

This module provides configuration classes for browser automation.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

@dataclass
class BrowserConfig:
    """Base configuration for browser instances."""
    
    # General settings
    headless: bool = False
    window_size: Tuple[int, int] = (1920, 1080)
    page_load_timeout: int = 30
    script_timeout: int = 30
    implicit_wait: int = 0
    
    # Performance options
    disable_gpu: bool = False
    no_sandbox: bool = True
    disable_dev_shm_usage: bool = True
    
    # Network settings
    proxy_server: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Security
    accept_insecure_certs: bool = False
    ignore_certificate_errors: bool = False
    
    # Experimental features
    experimental_options: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {k: v for k, v in self.__dict__.items() 
                if not k.startswith('_') and v is not None}


@dataclass
class ChromeConfig(BrowserConfig):
    """Chrome-specific browser configuration."""
    
    # Chrome-specific settings
    chrome_binary: Optional[str] = None
    chrome_driver_path: Optional[str] = None
    user_data_dir: Optional[str] = None
    download_dir: Optional[str] = None
    
    # Chrome features
    disable_extensions: bool = False
    disable_infobars: bool = True
    incognito: bool = False
    
    # Chrome preferences
    prefs: Dict[str, Any] = field(default_factory=dict)
    
    # Extensions
    extensions: List[Union[str, Path]] = field(default_factory=list)
    
    # Additional arguments
    arguments: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Ensure window_size is a tuple
        if isinstance(self.window_size, (list, tuple)) and len(self.window_size) == 2:
            self.window_size = tuple(map(int, self.window_size))
        
        # Set default preferences if download_dir is specified
        if self.download_dir and not self.prefs.get('download.default_directory'):
            self.prefs.update({
                'download.default_directory': str(Path(self.download_dir).absolute()),
                'download.prompt_for_download': False,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': True
            })
