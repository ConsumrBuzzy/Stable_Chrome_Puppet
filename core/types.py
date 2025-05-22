"""
Type definitions and type hints for Chrome Puppet.

This module contains type definitions and type hints used throughout the Chrome Puppet
codebase to improve code clarity and enable better static type checking.
"""
from typing import Dict, List, Optional, Tuple, Union, Any, TypedDict, Literal
from pathlib import Path

# Type aliases
BrowserType = Literal["chrome", "firefox", "safari", "edge"]
"""Supported browser types."""

WindowSize = Tuple[int, int]
"""Window size as (width, height) tuple."""

# Configuration type hints
class BrowserConfig(TypedDict, total=False):
    """Type hints for browser configuration."""
    headless: bool
    window_size: Optional[WindowSize]
    user_agent: Optional[str]
    download_dir: Optional[Union[str, Path]]
    implicit_wait: int
    timeout: int
    extra_args: List[str]
    experimental_options: Dict[str, Any]

# Element location strategies
class ByType:
    """Set of supported location strategies."""
    ID = "id"
    XPATH = "xpath"
    LINK_TEXT = "link text"
    PARTIAL_LINK_TEXT = "partial link text"
    NAME = "name"
    TAG_NAME = "tag name"
    CLASS_NAME = "class name"
    CSS_SELECTOR = "css selector"

# Export all types
__all__ = [
    'BrowserType',
    'WindowSize',
    'BrowserConfig',
    'ByType',
]
