"""
Browser feature modules for Chrome Puppet.

This package contains modular browser features that can be used independently
or composed together in browser implementations.

Modules:
    - element: Element interaction and querying
    - navigation: Page navigation and waiting
    - screenshot: Screenshot capture and management
"""

from .element import ElementHelper
from .navigation import NavigationMixin
from .screenshot import ScreenshotHelper

__all__ = [
    'ElementHelper',
    'NavigationMixin',
    'ScreenshotHelper'
]
