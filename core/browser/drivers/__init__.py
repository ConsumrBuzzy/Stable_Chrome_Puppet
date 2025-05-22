"""
Browser driver implementations for different browsers.

This package contains browser-specific implementations that adhere to the
BaseBrowserDriver interface. Each browser (Chrome, Firefox, etc.) should have
its own module in this package.
"""

from typing import Type, Dict, TypeVar, Any
from ..base import BaseBrowser

# Type variable for browser driver classes
T = TypeVar('T', bound='BaseBrowserDriver')

# Registry of available browser drivers
_registry: Dict[str, Type['BaseBrowserDriver']] = {}


def register_driver(name: str) -> callable:
    """Decorator to register a browser driver class.
    
    Args:
        name: Unique name for the browser driver
        
    Returns:
        Decorator function
    """
    def decorator(driver_class: Type[T]) -> Type[T]:
        if name in _registry:
            raise ValueError(f"Browser driver '{name}' is already registered")
        _registry[name] = driver_class
        return driver_class
    return decorator


def get_driver_class(name: str) -> Type['BaseBrowserDriver']:
    """Get a browser driver class by name.
    
    Args:
        name: Name of the browser driver to get
        
    Returns:
        The browser driver class
        
    Raises:
        ValueError: If the browser driver is not found
    """
    if name not in _registry:
        raise ValueError(f"No browser driver registered with name: {name}")
    return _registry[name]


class BaseBrowserDriver(BaseBrowser):
    """Base class for browser driver implementations.
    
    This class serves as the base for all browser-specific implementations.
    Each browser driver should implement the abstract methods defined here.
    """
    
    def __init__(self, config: Any, logger: Any = None):
        """Initialize the browser driver.
        
        Args:
            config: Configuration for the browser
            logger: Logger instance for logging
        """
        super().__init__(config, logger)
    
    @classmethod
    def get_name(cls) -> str:
        """Get the name of the browser driver.
        
        Returns:
            str: The name of the browser driver
        """
        raise NotImplementedError("Subclasses must implement get_name()")
    
    @classmethod
    def create(cls, config: Any, logger: Any = None) -> 'BaseBrowserDriver':
        """Create a new instance of the browser driver.
        
        Args:
            config: Configuration for the browser
            logger: Logger instance for logging
            
        Returns:
            A new instance of the browser driver
        """
        return cls(config, logger)


# Import browser drivers to register them
# This must be at the end of the file to avoid circular imports
from .chrome_driver import ChromeDriver  # noqa: F401

__all__ = [
    'BaseBrowserDriver',
    'register_driver',
    'get_driver_class',
]
