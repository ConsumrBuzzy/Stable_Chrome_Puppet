"""
Utility functions for Chrome Puppet.

This module provides various utility functions for file operations, logging,
and system information that are used throughout the Chrome Puppet project.
"""
import os
import sys
import logging
import platform
import datetime
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def get_default_download_dir() -> str:
    """Get the default download directory based on the operating system."""
    home = os.path.expanduser("~")
    system = platform.system().lower()
    
    if system == "windows":
        return os.path.join(home, "Downloads")
    elif system == "darwin":  # macOS
        return os.path.join(home, "Downloads")
    else:  # Linux and others
        return os.path.join(home, "Downloads")

def ensure_dir(directory: Union[str, Path]) -> str:
    """Ensure that a directory exists, creating it if necessary."""
    if isinstance(directory, str):
        directory = Path(directory)
    
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return str(directory.absolute())
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        raise

def is_chrome_installed() -> Tuple[bool, Optional[str]]:
    """Check if Chrome is installed and return its path."""
    system = platform.system().lower()
    
    if system == "windows":
        # Common Chrome installation paths on Windows
        paths = [
            os.path.expandvars(r"%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\\Google\\Chrome\\Application\\chrome.exe")
        ]
    elif system == "darwin":  # macOS
        paths = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:  # Linux and others
        paths = [
            "/usr/bin/google-chrome",
            "/usr/local/bin/chromium",
            "/usr/bin/chromium-browser"
        ]
    
    for path in paths:
        if os.path.isfile(path):
            return True, path
    
    return False, None

def get_chrome_version() -> Optional[str]:
    """Get the installed Chrome version."""
    try:
        import subprocess
        system = platform.system().lower()
        
        if system == "windows":
            cmd = 'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version'
    except Exception as e:
        logger.warning(f"Could not determine Chrome version: {e}", exc_info=True)
        return None

def setup_logger(
    name: str,
    log_level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    console: bool = True
) -> logging.Logger:
    """Set up and configure a logger.
    
    Args:
        name: Logger name
        log_level: Logging level (default: logging.INFO)
        log_file: Path to log file (optional)
        console: Whether to log to console (default: True)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear existing handlers if any
    logger.handlers = []
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add file handler if log_file is provided
    if log_file:
        ensure_dir(os.path.dirname(log_file) if os.path.dirname(log_file) else None)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler if console is True
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

def retry(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
    logger: Optional[logging.Logger] = None
):
    """Retry decorator for functions that may fail.
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts (default: 3)
        delay: Delay between attempts in seconds (default: 1.0)
        exceptions: Tuple of exceptions to catch (default: Exception)
        logger: Logger instance for logging retries (optional)
        
    Returns:
        Wrapped function with retry logic
    """
    import time
    
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if logger:
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed: {e}"
                    )
                if attempt < max_attempts:
                    time.sleep(delay)
        raise last_exception
    
    return wrapper

def get_timestamp(fmt: str = "%Y%m%d_%H%M%S") -> str:
    """Get current timestamp in the specified format.
    
    Args:
        fmt: Format string for the timestamp (default: "%Y%m%d_%H%M%S")
        
    Returns:
        Formatted timestamp string
    """
    return datetime.datetime.now().strftime(fmt)


def ensure_file(file_path: Union[str, Path], default_content: str = "") -> bool:
    """Ensure a file exists, creating it with default content if it doesn't.
    
    Args:
        file_path: Path to the file
        default_content: Default content to write if file is created
        
    Returns:
        bool: True if file exists or was created successfully, False otherwise
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            ensure_dir(file_path.parent)
            file_path.write_text(default_content, encoding='utf-8')
        return True
    except Exception as e:
        logger.error(f"Failed to ensure file {file_path}: {e}", exc_info=True)
        return False
