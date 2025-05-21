"""Chrome Puppet - A robust and extensible Chrome browser automation tool."""
from core.browser.puppet import ChromePuppet
from core.browser.chrome import ChromeConfig, DEFAULT_CONFIG
from core.browser.utils import get_chrome_version, is_chrome_installed

__version__ = "0.1.0"
__all__ = ['ChromePuppet', 'ChromeConfig', 'DEFAULT_CONFIG', 'get_chrome_version', 'is_chrome_installed']
