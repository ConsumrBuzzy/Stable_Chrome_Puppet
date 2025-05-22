"""Base driver interface for browser automation.

This module defines the abstract base class that all browser drivers must implement.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic

from ..types import BrowserConfig, BrowserType, BrowserOptions, BrowserService

T = TypeVar('T', bound='BaseDriver')


class BaseDriver(ABC, Generic[T]):
    """Abstract base class for browser drivers.
    
    This class defines the interface that all browser drivers must implement.
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None) -> None:
        """Initialize the browser driver with optional configuration.
        
        Args:
            config: Configuration for the browser instance.
        """
        self.config = config or BrowserConfig()
        self._service: Optional[BrowserService] = None
        self._options: Optional[BrowserOptions] = None
        self._is_running: bool = False
    
    @property
    def is_running(self) -> bool:
        """Check if the browser is currently running."""
        return self._is_running
    
    @abstractmethod
    def start(self) -> T:
        """Start the browser instance.
        
        Returns:
            Self for method chaining.
            
        Raises:
            BrowserError: If the browser fails to start.
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the browser instance and clean up resources."""
        pass
    
    @abstractmethod
    def get_browser_type(self) -> BrowserType:
        """Get the type of browser this driver manages.
        
        Returns:
            The browser type.
        """
        pass
    
    @abstractmethod
    def get_options(self) -> BrowserOptions:
        """Get the browser options.
        
        Returns:
            The browser options instance.
        """
        pass
    
    @abstractmethod
    def get_service(self) -> BrowserService:
        """Get the browser service instance.
        
        Returns:
            The browser service instance.
        """
        pass
    
    def __enter__(self) -> T:
        """Context manager entry point."""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit point."""
        self.stop()
    
    def __del__(self) -> None:
        """Ensure resources are cleaned up when the object is garbage collected."""
        if self.is_running:
            self.stop()
