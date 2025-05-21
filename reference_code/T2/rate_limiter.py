"""
Rate limiting implementation for DNC Genie.
Provides decorators and context managers for rate limiting.
"""
import time
from typing import Callable, Optional, List, Dict, Any
from functools import wraps
from datetime import datetime, timedelta
import logging

from exceptions import RateLimitExceededError
from config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    A simple token bucket rate limiter implementation.
    """
    
    def __init__(self, max_requests: int, period: float):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the period
            period: Time period in seconds
        """
        self.max_requests = max_requests
        self.period = period
        self.tokens = max_requests
        self.last_update = time.monotonic()
        self.lock = False  # Simple lock to prevent race conditions
        
    def _refill_tokens(self):
        """Refill tokens based on time passed."""
        now = time.monotonic()
        time_passed = now - self.last_update
        
        # Add tokens based on time passed
        self.tokens += time_passed * (self.max_requests / self.period)
        self.tokens = min(self.tokens, self.max_requests)
        self.last_update = now
    
    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            bool: True if tokens were acquired, False otherwise
        """
        while self.lock:
            time.sleep(0.01)  # Simple spin lock
            
        self.lock = True
        self._refill_tokens()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            self.lock = False
            return True
            
        self.lock = False
        return False
    
    def wait(self, tokens: int = 1):
        """
        Wait until tokens are available.
        
        Args:
            tokens: Number of tokens to acquire
            
        Raises:
            RateLimitExceededError: If waiting would take too long
        """
        start_time = time.monotonic()
        max_wait = self.period * 2  # Don't wait more than 2x the period
        
        while not self.acquire(tokens):
            if time.monotonic() - start_time > max_wait:
                raise RateLimitExceededError("Rate limit wait timeout")
            time.sleep(0.1)

# Global rate limiter instance
default_rate_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_REQUESTS,
    period=settings.RATE_LIMIT_PERIOD
)

def rate_limited(max_requests: int = None, period: float = None):
    """
    Decorator to rate limit function calls.
    
    Args:
        max_requests: Maximum number of requests allowed in the period
        period: Time period in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func):
        limiter = RateLimiter(
            max_requests or settings.RATE_LIMIT_REQUESTS,
            period or settings.RATE_LIMIT_PERIOD
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.wait()
            return func(*args, **kwargs)
            
        return wrapper
    return decorator

class RateLimitContext:
    """Context manager for rate limiting."""
    
    def __init__(self, max_requests: int = None, period: float = None):
        self.limiter = RateLimiter(
            max_requests or settings.RATE_LIMIT_REQUESTS,
            period or settings.RATE_LIMIT_PERIOD
        )
    
    def __enter__(self):
        self.limiter.wait()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
