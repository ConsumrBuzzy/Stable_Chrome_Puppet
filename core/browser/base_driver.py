"""
Base driver module for browser automation.

This module provides the BaseDriver class that serves as the foundation
for all browser driver implementations.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

from ..config import BrowserConfig

T = TypeVar('T', bound='BaseDriver')


class BaseDriver(Generic[T], ABC):
    """Base class for all browser drivers.
    
    This class defines the common interface that all browser drivers must implement.
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None) -> None:
        """Initialize the base driver with configuration.
        
        Args:
            config: Configuration for the browser instance.
        """
        self.config = config or BrowserConfig()
        self._driver: Any = None
        self._service: Any = None
        self._options: Any = None
    
    @abstractmethod
    def start(self) -> T:
        """Start the browser instance.
        
        Returns:
            Self: The instance of the browser driver.
        """
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the browser instance and clean up resources."""
        pass
    
    @property
    def driver(self) -> Any:
        """Get the underlying WebDriver instance.
        
        Returns:
            The WebDriver instance.
            
        Raises:
            RuntimeError: If the driver is not initialized.
        """
        if self._driver is None:
            raise RuntimeError("Browser is not running. Call start() first.")
        return self._driver
    
    def __enter__(self) -> T:
        """Context manager entry point."""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit point."""
        self.stop()
