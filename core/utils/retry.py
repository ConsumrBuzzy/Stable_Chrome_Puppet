"""
Retry decorators for handling transient failures.

This module provides decorators for retrying functions that may fail temporarily.
"""
import time
import random
from functools import wraps
from typing import Any, Callable, Type, Tuple, Union, TypeVar, Optional

T = TypeVar('T')


def retry_on_exception(
    max_retries: int = 3,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    backoff_factor: float = 1.0,
    max_delay: float = 60.0,
    logger: Optional[Callable[[str], None]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorate a function to retry on specified exceptions.
    
    Args:
        max_retries: Maximum number of retries before giving up
        exceptions: Exception(s) to catch and retry on
        backoff_factor: Multiplier for exponential backoff between retries
        max_delay: Maximum delay between retries in seconds
        logger: Optional logger function for retry attempts
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            retries = 0
            last_exception = None
            
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    retries += 1
                    
                    if retries > max_retries:
                        break
                        
                    # Calculate delay with exponential backoff and jitter
                    delay = min(
                        backoff_factor * (2 ** (retries - 1)) * (0.5 * (1 + random.random())),
                        max_delay
                    )
                    
                    if logger:
                        logger(
                            f"Attempt {retries}/{max_retries} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                    
                    time.sleep(delay)
            
            # If we get here, all retries failed
            raise type(last_exception)(
                f"Function {func.__name__} failed after {max_retries} retries. "
                f"Last error: {last_exception}"
            ) from last_exception
            
        return wrapper
    return decorator


def retry_with_timeout(
    timeout: float = 60.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    check_interval: float = 1.0,
    logger: Optional[Callable[[str], None]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorate a function to retry until success or timeout.
    
    Args:
        timeout: Maximum time in seconds to keep retrying
        exceptions: Exception(s) to catch and retry on
        check_interval: Time to wait between retries in seconds
        logger: Optional logger function for retry attempts
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.monotonic()
            attempts = 0
            last_exception = None
            
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    attempts += 1
                    
                    elapsed = time.monotonic() - start_time
                    if elapsed >= timeout:
                        break
                        
                    if logger:
                        logger(
                            f"Attempt {attempts} failed: {e}. "
                            f"Retrying in {check_interval:.2f}s... "
                            f"({timeout - elapsed:.1f}s remaining)"
                        )
                    
                    time.sleep(check_interval)
            
            # If we get here, we timed out
            raise TimeoutError(
                f"Function {func.__name__} timed out after {timeout:.1f}s "
                f"({attempts} attempts). Last error: {last_exception}"
            ) from last_exception
            
        return wrapper
    return decorator
