"""Chrome Puppet - A robust and extensible Chrome browser automation tool."""
from core.browser.drivers.chrome_driver import ChromeDriver
from core.browser.config import ChromeConfig, DEFAULT_CONFIG
from utils.utils import get_chrome_version, is_chrome_installed

__version__ = "0.2.0"
__all__ = ['ChromeDriver', 'ChromeConfig', 'DEFAULT_CONFIG', 'get_chrome_version', 'is_chrome_installed']
