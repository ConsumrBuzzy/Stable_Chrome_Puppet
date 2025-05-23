"""
Configuration settings for Chrome browser automation.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class ChromeConfig:
    """Configuration for Chrome browser instance."""
    
    # Browser settings
    headless: bool = False
    window_size: str = "1920,1080"
    user_data_dir: Optional[str] = None
    
    # Timeouts (in seconds)
    page_load_timeout: int = 30
    script_timeout: int = 30
    implicit_wait: int = 0
    
    # Performance options
    disable_gpu: bool = False
    no_sandbox: bool = True
    disable_dev_shm_usage: bool = True
    disable_extensions: bool = False
    disable_infobars: bool = True
    
    # Network settings
    proxy_server: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Security
    accept_insecure_certs: bool = False
    ignore_certificate_errors: bool = False
    
    def get_window_size(self) -> Tuple[int, int]:
        """Parse window size string into width and height tuple."""
        try:
            width, height = map(int, self.window_size.split(','))
            return max(800, width), max(600, height)  # Ensure minimum size
        except (ValueError, AttributeError):
            return 1920, 1080  # Default size
