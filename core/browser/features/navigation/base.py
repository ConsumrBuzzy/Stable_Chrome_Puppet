"""Base classes for navigation functionality."""
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, Union, List

class BaseNavigation(ABC):
    """Base class for navigation functionality."""
    
    @abstractmethod
    def get(self, url: str) -> None:
        """Navigate to a URL.
        
        Args:
            url: The URL to navigate to
        """
        pass
    
    @abstractmethod
    def back(self) -> None:
        """Go back to the previous page in browser history."""
        pass
    
    @abstractmethod
    def forward(self) -> None:
        """Go forward to the next page in browser history."""
        pass
    
    @abstractmethod
    def refresh(self) -> None:
        """Refresh the current page."""
        pass
    
    @abstractmethod
    def get_current_url(self) -> str:
        """Get the current URL.
        
        Returns:
            The current URL as a string
        """
        pass
    
    @abstractmethod
    def get_title(self) -> str:
        """Get the current page title.
        
        Returns:
            The current page title
        """
        pass
