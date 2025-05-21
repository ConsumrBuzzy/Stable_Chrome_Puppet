"""Utility functions for Chrome Puppet."""
import os
import sys
import logging
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union

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
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True)
            version = result.strip().split()[-1]
            return version
        elif system == "darwin":  # macOS
            cmd = "/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --version"
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True)
            return result.strip().split()[-1]
        else:  # Linux
            cmd = "google-chrome --version"
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, text=True)
            return result.strip().split()[-1]
    except Exception as e:
        logger.warning(f"Could not determine Chrome version: {e}")
        return None
