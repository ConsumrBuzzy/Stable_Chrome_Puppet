"""
Configuration settings for Chrome Puppet.

This module defines the configuration classes used throughout the Chrome Puppet
application to manage browser settings and behavior.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

@dataclass
class ChromeConfig:
    """Configuration settings for Chrome browser automation."""
    
    # Browser settings
    headless: bool = True
    """Whether to run Chrome in headless mode."""
    
    window_size: Optional[Tuple[int, int]] = (1920, 1080)
    """Window size as (width, height) tuple. If None, browser will be maximized."""
    
    user_agent: Optional[str] = None
    """Custom user agent string. If None, uses Chrome's default."""
    
    download_dir: Optional[str] = None
    """Directory to save downloads. If None, uses system default."""
    
    chrome_type: str = "chrome"
    """Type of Chrome browser to use (chrome, chrome-beta, chrome-dev, etc.)."""
    
    chrome_path: Optional[str] = None
    """Path to the Chrome/Chromium executable. If None, uses the default path."""
    
    chromium: bool = False
    """Whether to use Chromium instead of Chrome."""
    
    implicit_wait: int = 10
    """Implicit wait time in seconds for element location."""
    
    timeout: int = 30
    """Default timeout in seconds for page loads and element waits."""
    
    # Advanced settings
    chrome_options: Dict[str, Any] = field(default_factory=dict)
    """Additional Chrome options to pass to WebDriver."""
    
    chrome_arguments: List[str] = field(default_factory=lambda: [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--remote-debugging-port=9222",
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars"
    ])
    """Command line arguments to pass to Chrome."""
    
    extensions: List[str] = field(default_factory=list)
    """List of Chrome extension paths to install."""
    
    experimental_options: Dict[str, Any] = field(default_factory=dict)
    """Experimental Chrome options to pass to WebDriver."""
    
    window_size: Optional[Tuple[int, int]] = (1920, 1080)
    """Window size as (width, height) tuple. If None, browser will be maximized."""
    
    # Logging and debugging
    verbose: bool = False
    """Enable verbose logging."""
    
    log_file: Optional[str] = None
    """Path to log file. If None, logs to console only."""
    
    # Performance settings
    disable_gpu: bool = True
    """Disable GPU hardware acceleration."""
    
    no_sandbox: bool = True
    """Disable Chrome sandboxing (required in some environments)."""
    
    disable_dev_shm_usage: bool = True
    """Overcome limited resource problems in Docker containers."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            key: value for key, value in self.__dict__.items() 
            if not key.startswith('_')
        }

# Default configuration
DEFAULT_CONFIG = ChromeConfig()

__all__ = ['ChromeConfig', 'DEFAULT_CONFIG']
