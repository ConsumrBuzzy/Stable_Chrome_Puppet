"""System information collection utilities."""
import platform
import sys
import subprocess
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def get_system_info() -> Dict[str, Any]:
    """
    Collect system information including OS, architecture, Python version,
    and Chrome/ChromeDriver versions.
    
    Returns:
        Dict containing system information
    """
    info = {
        'os': {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'is_64bit': sys.maxsize > 2**32,
        },
        'python': {
            'version': platform.python_version(),
            'implementation': platform.python_implementation(),
            'executable': sys.executable,
        },
        'chrome': {},
        'chromedriver': {},
    }
    
    # Get Chrome version
    try:
        if platform.system() == 'Windows':
            cmd = r'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, check=False)
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1]
                info['chrome']['version'] = version
    except Exception as e:
        logger.warning(f"Could not determine Chrome version: {e}")
    
    return info

def log_system_info() -> None:
    """Log system information at the beginning of the session."""
    info = get_system_info()
    
    logger.info("=" * 80)
    logger.info("System Information:")
    logger.info(f"OS: {info['os']['system']} {info['os']['release']} ({info['os']['version']})")
    logger.info(f"Architecture: {info['os']['machine']} (64-bit: {info['os']['is_64bit']})")
    logger.info(f"Processor: {info['os']['processor']}")
    logger.info(f"Python: {info['python']['version']} ({info['python']['implementation']})")
    
    if 'version' in info['chrome']:
        logger.info(f"Chrome version: {info['chrome']['version']}")
    else:
        logger.warning("Chrome version not detected")
    
    logger.info("=" * 80)
