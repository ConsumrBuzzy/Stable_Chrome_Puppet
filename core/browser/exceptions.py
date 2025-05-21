"""Custom exceptions for the browser automation framework."""

class BrowserError(Exception):
    """Base exception for all browser-related errors."""
    pass

class BrowserNotInitializedError(BrowserError):
    """Raised when browser is not properly initialized."""
    pass

class NavigationError(BrowserError):
    """Raised when there's an error during page navigation."""
    pass

class ElementNotFoundError(BrowserError):
    """Raised when an element cannot be found."""
    pass

class ElementNotInteractableError(BrowserError):
    """Raised when an element is not interactable."""
    pass

class TimeoutError(BrowserError):
    """Raised when an operation times out."""
    pass

class ScreenshotError(BrowserError):
    """Raised when there's an error taking a screenshot."""
    pass
