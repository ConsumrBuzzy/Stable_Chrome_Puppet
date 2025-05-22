"""
Profile management for browser automation.

This package provides functionality to manage browser profiles,
including listing, validating, and selecting profiles.
"""

from .manager import ProfileManager
from .profile import Profile

__all__ = ['ProfileManager', 'Profile']
