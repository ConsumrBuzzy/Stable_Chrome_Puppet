"""Configuration settings for Chrome Puppet."""
import os
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from webdriver_manager.core.utils import ChromeType

@dataclass
class ChromeConfig:
    """Configuration for Chrome browser instance."""
    headless: bool = True
    window_size: tuple = (1920, 1080)
    user_agent: str = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    timeout: int = 30  # seconds
    chrome_type: ChromeType = ChromeType.GOOGLE
    chrome_path: Optional[str] = None
    download_dir: Optional[str] = None
    proxy: Optional[Dict[str, str]] = None
    extensions: List[str] = field(default_factory=list)
    experimental_options: Dict[str, Any] = field(default_factory=dict)
    chrome_arguments: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Convert string paths to Path objects
        if self.chrome_path and isinstance(self.chrome_path, str):
            self.chrome_path = os.path.abspath(os.path.expanduser(self.chrome_path))
        if self.download_dir and isinstance(self.download_dir, str):
            self.download_dir = os.path.abspath(os.path.expanduser(self.download_dir))

# Default configuration
DEFAULT_CONFIG = ChromeConfig()
