""
Site-specific handlers for different websites.

This package contains implementations of BaseSiteHandler for various websites.
Each module should implement a handler for a specific website or web application.
"""
from pathlib import Path
from typing import Type, Dict, TypeVar, Optional

from .base_site import BaseSiteHandler
from .example_site import ExampleSiteHandler

# Type variable for site handlers
SiteHandlerT = TypeVar('SiteHandlerT', bound=BaseSiteHandler)

# Registry of available site handlers
SITE_HANDLERS: Dict[str, Type[BaseSiteHandler]] = {
    'example': ExampleSiteHandler,
    # Add new site handlers here
}

def get_site_handler(site_name: str) -> Optional[Type[BaseSiteHandler]]:
    """Get a site handler class by name.
    
    Args:
        site_name: The name of the site handler to get
        
    Returns:
        The site handler class, or None if not found
    """
    return SITE_HANDLERS.get(site_name.lower())

def register_site_handler(site_name: str, handler_class: Type[BaseSiteHandler]) -> None:
    """Register a new site handler.
    
    Args:
        site_name: The name to register the handler under
        handler_class: The handler class to register
    """
    SITE_HANDLERS[site_name.lower()] = handler_class

__all__ = [
    'BaseSiteHandler',
    'ExampleSiteHandler',
    'get_site_handler',
    'register_site_handler',
    'SITE_HANDLERS'
]
