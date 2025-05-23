"""
Browser automation interface and implementations.

This module provides a high-level interface for browser automation
with specific implementations for different browsers.
"""

from typing import Optional, Protocol, runtime_checkable
from selenium.webdriver.remote.webdriver import WebDriver

@runtime_checkable
class Browser(Protocol):
    """Protocol defining the browser automation interface."""
    
    def get(self, url: str) -> None:
        """Navigate to the specified URL."""
        ...
        
    @property
    def title(self) -> str:
        """Get the current page title."""
        ...
        
    @property
    def current_url(self) -> str:
        """Get the current URL."""
        ...
        
    def execute_script(self, script: str, *args) -> object:
        """Execute JavaScript in the current page context."""
        ...
        
    def close(self) -> None:
        """Close the browser and release resources."""
        ...
        
    def __enter__(self):
        """Context manager entry."""
        ...
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        ...
