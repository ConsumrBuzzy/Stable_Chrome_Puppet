"""Browser factory for creating browser instances."""
import importlib
import logging
from typing import Optional, Type, Dict, Any

from .interfaces import IBrowser, IBrowserFactory

class BrowserFactory(IBrowserFactory):
    """Factory for creating browser instances."""
    
    _browser_registry: Dict[str, Type[IBrowser]] = {}
    
    @classmethod
    def register_browser(cls, name: str, browser_class: Type[IBrowser]) -> None:
        """Register a browser class with the factory.
        
        Args:
            name: Name to register the browser under
            browser_class: Browser class to register
        """
        if not issubclass(browser_class, IBrowser):
            raise TypeError(f"{browser_class.__name__} must implement IBrowser")
        cls._browser_registry[name.lower()] = browser_class
    
    @classmethod
    def create_browser(
        cls,
        browser_type: str,
        config: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
        **kwargs
    ) -> IBrowser:
        """Create a new browser instance.
        
        Args:
            browser_type: Type of browser to create (e.g., 'chrome')
            config: Configuration for the browser
            logger: Logger instance to use
            **kwargs: Additional arguments to pass to the browser constructor
            
        Returns:
            A new browser instance
            
        Raises:
            ValueError: If the browser type is not registered
        """
        browser_type = browser_type.lower()
        if browser_type not in cls._browser_registry:
            raise ValueError(f"Unknown browser type: {browser_type}")
            
        browser_class = cls._browser_registry[browser_type]
        return browser_class(config=config, logger=logger, **kwargs)
    
    @classmethod
    def get_available_browsers(cls) -> list[str]:
        """Get a list of available browser types.
        
        Returns:
            List of registered browser type names
        """
        return list(cls._browser_registry.keys())


def register_browser(name: str) -> callable:
    """Decorator to register a browser class with the factory.
    
    Args:
        name: Name to register the browser under
    """
    def decorator(cls: Type[IBrowser]) -> Type[IBrowser]:
        BrowserFactory.register_browser(name, cls)
        return cls
    return decorator


def auto_discover_browsers() -> None:
    """Auto-discover and register browser implementations."""
    import pkgutil
    from pathlib import Path
    
    # Get the directory containing browser implementations
    browser_dir = Path(__file__).parent / "drivers"
    
    # Import all modules in the drivers directory
    for finder, name, ispkg in pkgutil.iter_modules([str(browser_dir)]):
        if not ispkg:
            continue
            
        try:
            module_name = f"core.browser.drivers.{name}"
            importlib.import_module(module_name)
        except ImportError as e:
            logging.warning(f"Failed to import browser module {name}: {e}")
            continue
