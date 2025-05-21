"""
exceptions.py - Custom exceptions for Zoom DNC Genie
"""

class ZoomLoginFailedException(Exception):
    """Raised when login to Zoom fails after retries."""
    pass

class CaptchaDetectedException(Exception):
    """Raised when a reCAPTCHA or similar challenge is detected."""
    pass

class ElementNotFoundException(Exception):
    """Raised when a required web element is not found."""
    pass
