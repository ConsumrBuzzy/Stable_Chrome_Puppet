"""Storage management module.

This module provides functionality for managing browser storage.

Submodules:
    - cookies: Cookie management
    - local_storage: Local storage management
"""

from .cookies import Cookie, CookieManagerMixin

__all__ = [
    'Cookie',
    'CookieManagerMixin'
]
