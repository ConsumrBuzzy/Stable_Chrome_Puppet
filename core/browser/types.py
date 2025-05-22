"""
Type definitions for browser automation components.

This module contains type hints and protocols used throughout the browser automation
package to ensure type safety and improve code maintainability.
"""
from typing import Any, Dict, List, NamedTuple, Optional, Protocol, Tuple, Union
from pathlib import Path
from enum import Enum, auto


class BrowserType(Enum):
    """Supported browser types."""
    CHROME = auto()
    FIREFOX = auto()
    EDGE = auto()
    SAFARI = auto()


class WindowSize(NamedTuple):
    """Represents browser window dimensions."""
    width: int
    height: int


class BrowserOptions(Protocol):
    """Protocol for browser configuration options."""
    headless: bool
    window_size: WindowSize
    user_agent: Optional[str]
    accept_insecure_certs: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert options to a dictionary."""
        ...


class NavigationTiming(NamedTuple):
    """Timing information for page navigation."""
    start_time: float
    dom_content_loaded: float
    load: float
    dom_complete: float


class BrowserState(Enum):
    """Represents the current state of the browser."""
    CREATED = auto()
    RUNNING = auto()
    NAVIGATING = auto()
    READY = auto()
    ERROR = auto()
    CLOSED = auto()


class ElementState(Enum):
    """Possible states of a web element."""
    PRESENT = auto()
    VISIBLE = auto()
    CLICKABLE = auto()
    STALE = auto()
    HIDDEN = auto()


# Type aliases
Url = str
XPath = str
CssSelector = str
ElementSelector = Union[str, XPath, CssSelector]
ScreenshotFormat = str  # Should be one of: 'png', 'jpeg', 'webp'

__all__ = [
    'BrowserType',
    'WindowSize',
    'BrowserOptions',
    'NavigationTiming',
    'BrowserState',
    'ElementState',
    'Url',
    'XPath',
    'CssSelector',
    'ElementSelector',
    'ScreenshotFormat',
]
