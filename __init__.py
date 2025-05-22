"""Chrome Puppet - A robust and extensible Chrome browser automation tool."""
__version__ = "0.2.0"

# Lazy imports to prevent circular imports
ChromeDriver = None
ChromeConfig = None
DEFAULT_CONFIG = None

def _import_chrome_driver():
    """Lazy import for ChromeDriver."""
    global ChromeDriver
    if ChromeDriver is None:
        from core.browser.drivers.chrome_driver import ChromeDriver as CD
        ChromeDriver = CD
    return ChromeDriver

def _import_config():
    """Lazy import for ChromeConfig and DEFAULT_CONFIG."""
    global ChromeConfig, DEFAULT_CONFIG
    if ChromeConfig is None or DEFAULT_CONFIG is None:
        from core.config import ChromeConfig as CC, DEFAULT_CONFIG as DC
        ChromeConfig = CC
        DEFAULT_CONFIG = DC
    return ChromeConfig, DEFAULT_CONFIG

def get_chrome_version():
    """Get the installed Chrome version."""
    from utils.utils import get_chrome_version as gcv
    return gcv()

def is_chrome_installed():
    """Check if Chrome is installed."""
    from utils.utils import is_chrome_installed as ici
    return ici()

__all__ = [
    'ChromeDriver',
    'ChromeConfig',
    'DEFAULT_CONFIG',
    'get_chrome_version',
    'is_chrome_installed'
]
