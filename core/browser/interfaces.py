"""Browser interfaces and abstract base classes."""
from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, Type
import logging

T = TypeVar('T', bound='IBrowser')

class IBrowser(ABC):
    """Interface for browser operations."""
    
    @abstractmethod
    def start(self) -> None:
        """Start the browser instance."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the browser instance."""
        pass
    
    @abstractmethod
    def navigate_to(self, url: str, wait_time: Optional[float] = None) -> bool:
        """Navigate to the specified URL."""
        pass
    
    @abstractmethod
    def get_page_source(self) -> str:
        """Get the current page source."""
        pass
    
    @abstractmethod
    def get_current_url(self) -> str:
        """Get the current URL."""
        pass
    
    @abstractmethod
    def take_screenshot(self, file_path: str, full_page: bool = False) -> bool:
        """Take a screenshot of the current page."""
        pass
    
    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Check if the browser is running."""
        pass


class IBrowserFactory(ABC):
    """Interface for browser factory."""
    
    @abstractmethod
    def create_browser(self, *args, **kwargs) -> IBrowser:
        """Create a new browser instance."""
        pass
