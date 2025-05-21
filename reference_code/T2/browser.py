"""
Robust WebDriver setup for DNC Genie, refactored from T1 reference.
Uses utils.browser_utils.create_driver for fallback, stealth, and config/env support.
See reference/legacy_code/T1/utils/browser_utils.py for original logic.
"""
from utils.browser_utils import create_driver

def get_driver(use_uc=None):
    """
    Wrapper for robust Selenium driver creation.
    Set use_uc=True to enable stealth automation (undetected-chromedriver), or configure via USE_UC env var.
    """
    return create_driver(use_uc=use_uc)
