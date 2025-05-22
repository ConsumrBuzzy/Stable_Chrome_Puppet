"""Browser history management."""
from typing import List, Optional, Dict, Any

class NavigationHistoryMixin:
    """Mixin class providing browser history functionality."""
    
    def back(self) -> None:
        """Go back to the previous page in browser history."""
        self.driver.back()
    
    def forward(self) -> None:
        """Go forward to the next page in browser history."""
        self.driver.forward()
    
    def refresh(self) -> None:
        """Refresh the current page."""
        self.driver.refresh()
    
    def get_current_url(self) -> str:
        """Get the current URL.
        
        Returns:
            The current URL as a string
        """
        return self.driver.current_url
    
    def get_title(self) -> str:
        """Get the current page title.
        
        Returns:
            The current page title
        """
        return self.driver.title
