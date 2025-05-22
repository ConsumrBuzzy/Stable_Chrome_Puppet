"""Navigation module.

This module provides functionality for navigating between pages and waiting for page loads.

Submodules:
    - base: Base classes for navigation functionality
    - history: Browser history management
    - waiter: Page load waiting functionality
"""

from .base import BaseNavigation
from .history import NavigationHistoryMixin
from .waiter import NavigationWaitMixin

__all__ = [
    'BaseNavigation',
    'NavigationHistoryMixin',
    'NavigationWaitMixin'
]
