"""
Chrome driver configuration module.

This module provides backward compatibility by re-exporting the ChromeConfig
from the main configuration module.
"""

# Re-export ChromeConfig from the main config module
from core.config.chrome import ChromeConfig

__all__ = ['ChromeConfig']
