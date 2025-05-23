"""
Orchestrator for Chrome Puppet.

This module provides the main entry point for Chrome Puppet operations,
handling the coordination between different components.
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .drivers.chrome import ChromeBrowser
from .config import ChromeConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class ChromePuppetOrchestrator:
    """Orchestrates Chrome Puppet operations."""

    def __init__(self, config: Optional[ChromeConfig] = None) -> None:
        """Initialize the orchestrator with configuration.
        
        Args:
            config: Configuration for Chrome Puppet. Uses defaults if None.
        """
        self.config = config or DEFAULT_CONFIG
        self.browser: Optional[ChromeBrowser] = None

    def start_browser(self) -> None:
        """Start the Chrome browser instance."""
        if self.browser is not None:
            logger.warning("Browser is already running")
            return
            
        try:
            logger.info("Starting Chrome browser...")
            self.browser = ChromeBrowser(config=self.config)
            self.browser.start()
            logger.info("Chrome browser started successfully")
        except Exception as e:
            logger.error(f"Failed to start Chrome browser: {e}", exc_info=True)
            self.browser = None
            raise

    def stop_browser(self) -> None:
        """Stop the Chrome browser instance if it's running."""
        if self.browser is not None:
            try:
                logger.info("Stopping Chrome browser...")
                self.browser.stop()
                logger.info("Chrome browser stopped successfully")
            except Exception as e:
                logger.error(f"Error while stopping browser: {e}", exc_info=True)
            finally:
                self.browser = None

    def load_url(self, url: str, wait_time: Optional[int] = None) -> bool:
        """Load a URL in the browser.
        
        Args:
            url: The URL to load
            wait_time: Time in seconds to wait for page load. If None, uses config value.
            
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        if self.browser is None:
            self.start_browser()
            
        try:
            # Convert wait_time to milliseconds for Selenium
            timeout = (wait_time or self.config.page_load_timeout) * 1000 if wait_time is not None or hasattr(self.config, 'page_load_timeout') else 30000
            
            # Use the driver's get method directly
            self.browser.driver.get(url)
            
            # Wait for the page to load completely
            self.browser.driver.set_page_load_timeout(timeout / 1000)  # Convert back to seconds
            return True
            
        except Exception as e:
            logger.error(f"Error loading URL {url}: {e}", exc_info=True)
            return False
    
    def execute_task(self, task: str, **kwargs: Any) -> Any:
        """Execute a browser automation task.
        
        Args:
            task: Name of the task to execute
            **kwargs: Additional arguments for the task
            
        Returns:
            Result of the task execution
            
        Raises:
            ValueError: If the task is not recognized
        """
        if self.browser is None:
            self.start_browser()
            
        # Handle common tasks
        if task == 'load_url':
            return self.load_url(**kwargs)
            
        # Check if the task is a WebDriver method
        if hasattr(self.browser.driver, task):
            method = getattr(self.browser.driver, task)
            return method(**kwargs)
            
        # Check if the task is a ChromeBrowser method
        if hasattr(self.browser, task):
            method = getattr(self.browser, task)
            return method(**kwargs)
            
        raise ValueError(f"Unknown task: {task}")

    def __enter__(self):
        """Context manager entry."""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_browser()
        return False  # Don't suppress exceptions


def create_orchestrator(config: Optional[Union[Dict[str, Any], ChromeConfig]] = None) -> ChromePuppetOrchestrator:
    """Create a new ChromePuppetOrchestrator instance.
    
    Args:
        config: Configuration as a dict or ChromeConfig instance.
               If None, uses default configuration.
        
    Returns:
        Configured ChromePuppetOrchestrator instance
        
    Raises:
        ValueError: If the configuration is invalid
    """
    if config is None:
        return ChromePuppetOrchestrator()
        
    if isinstance(config, dict):
        # Filter out None values from the config dictionary
        filtered_config = {k: v for k, v in config.items() if v is not None}
        return ChromePuppetOrchestrator(ChromeConfig(**filtered_config))
        
    if isinstance(config, ChromeConfig):
        return ChromePuppetOrchestrator(config)
        
    raise ValueError("config must be a dict or ChromeConfig instance")
