"""
exceptions.py
Centralizes custom exceptions for DNC Genie automation.
"""

class DNCGenieError(Exception):
    """Base exception for all DNC Genie errors."""
    pass

class LoginError(DNCGenieError):
    """Raised when login to Zoom fails after all retries."""
    pass

class DNCError(DNCGenieError):
    """Base class for DNC operation errors."""
    pass

class DNCOperationError(DNCError):
    """Raised when a DNC operation fails."""
    pass

class BrowserError(DNCGenieError):
    """Raised for browser-related errors."""
    pass

class AuthenticationError(DNCGenieError):
    """Raised for authentication-related errors."""
    pass

class RateLimitExceededError(DNCGenieError):
    """Raised when the rate limit is exceeded."""
    pass

def handle_error(error: Exception, message: str = None) -> None:
    """Handle and log errors consistently."""
    error_message = f"{message}: {str(error)}" if message else str(error)
    raise error.__class__(error_message) from error
