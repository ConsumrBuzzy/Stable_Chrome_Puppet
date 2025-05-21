"""
Base class for site-specific handlers.

This module provides an abstract base class that defines the interface for
site-specific handlers. Each website or web portal should implement its own
handler by subclassing BaseSiteHandler.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path

from ..browser.chrome import ChromeBrowser
from ..config import ChromeConfig


class BaseSiteHandler(ABC):
    """Abstract base class for site-specific handlers.
    
    This class defines the interface that all site handlers must implement.
    """
    
    def __init__(self, 
                 config: Optional[ChromeConfig] = None, 
                 data_dir: Optional[Path] = None):
        """Initialize the site handler.
        
        Args:
            config: Chrome configuration to use. If None, uses default config.
            data_dir: Directory to store site-specific data (cookies, cache, etc.)
        """
        self.config = config or ChromeConfig()
        self.data_dir = data_dir or Path.cwd() / 'data' / self.get_site_name()
        self.browser: Optional[ChromeBrowser] = None
        self._setup_data_dir()
    
    @abstractmethod
    def get_site_name(self) -> str:
        """Return a unique identifier for the site (e.g., 'twitter', 'facebook')."""
        pass
    
    @abstractmethod
    def get_base_url(self) -> str:
        """Return the base URL of the site."""
        pass
    
    @abstractmethod
    def is_logged_in(self) -> bool:
        """Check if the user is logged in to the site."""
        pass
    
    @abstractmethod
    def login(self, username: str, password: str, **kwargs) -> bool:
        """Log in to the site.
        
        Args:
            username: Username or email
            password: Password
            **kwargs: Additional login parameters
            
        Returns:
            bool: True if login was successful
        """
        pass
    
    @abstractmethod
    def logout(self) -> None:
        """Log out of the site."""
        pass
    
    def _setup_data_dir(self) -> None:
        """Create the data directory if it doesn't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def start_browser(self) -> ChromeBrowser:
        """Start the browser and return the instance."""
        if self.browser is None or not self.browser.is_running():
            self.browser = ChromeBrowser(config=self.config)
            self.browser.start()
        return self.browser
    
    def stop_browser(self) -> None:
        """Stop the browser if it's running."""
        if self.browser and self.browser.is_running():
            self.browser.stop()
    
    def save_cookies(self, filename: str = 'cookies.pkl') -> Path:
        """Save browser cookies to a file."""
        if not self.browser:
            raise RuntimeError("Browser not started")
        cookies_file = self.data_dir / filename
        self.browser.save_cookies(str(cookies_file))
        return cookies_file
    
    def load_cookies(self, filename: str = 'cookies.pkl') -> bool:
        """Load cookies from a file."""
        if not self.browser:
            raise RuntimeError("Browser not started")
        cookies_file = self.data_dir / filename
        if cookies_file.exists():
            self.browser.load_cookies(str(cookies_file))
            return True
        return False
    
    def __enter__(self):
        """Context manager entry."""
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure browser is closed."""
        self.stop_browser()
    
    def __del__(self):
        """Ensure browser is closed when the object is destroyed."""
        self.stop_browser()
