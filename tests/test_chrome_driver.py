"""Tests for the ChromeDriver implementation."""
import os
import sys
import time
import pytest
import logging
from pathlib import Path
from typing import Generator, Any, Dict

# Import core module for lazy imports
import core
from core.browser.exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError
)
from core.browser.config import ChromeConfig

# Lazy imports
def get_chrome_driver():
    """Get the ChromeDriver class with lazy import."""
    if core.ChromeDriver is None:
        core._import_chrome_driver()
    return core.ChromeDriver

def get_chrome_config():
    """Get the ChromeConfig class with lazy import."""
    if core.ChromeConfig is None:
        core._import_config()
    return core.ChromeConfig

def get_driver_config():
    """Get the DriverConfig class with lazy import."""
    if core.DriverConfig is None:
        core._import_config()
    return core.DriverConfig

# Mark all tests in this module as browser tests
pytestmark = [pytest.mark.browser, pytest.mark.driver]

class TestChromeDriver:
    """Test cases for ChromeDriver class."""
    
    @pytest.fixture
    def chrome_config(self) -> 'core.ChromeConfig':
        """Create a ChromeConfig fixture for testing."""
        ChromeConfig = get_chrome_config()
        DriverConfig = get_driver_config()
        
        return ChromeConfig(
            headless=True,
            window_size=(1024, 768),
            chrome_args=[
                '--disable-notifications',
                '--disable-infobars',
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ],
            driver_config=DriverConfig(
                service_log_path='chromedriver.log'
            )
        )

    @pytest.fixture
    def chrome_driver(self, chrome_config) -> 'Generator[ChromeDriver, None, None]':
        """Create and yield a ChromeDriver instance for testing."""
        ChromeDriver = get_chrome_driver()
        driver = ChromeDriver(config=chrome_config)
        try:
            driver.start()
            yield driver
        finally:
            driver.stop()

    def test_initialization(self, chrome_config):
        """Test that ChromeDriver initializes correctly."""
        ChromeDriver = get_chrome_driver()
        driver = ChromeDriver(chrome_config)
        assert driver is not None
        assert driver.driver is not None
        assert driver.config == chrome_config
        driver.quit()

    def test_navigation(self, chrome_config):
        """Test basic navigation functionality."""
        ChromeDriver = get_chrome_driver()
        driver = ChromeDriver(chrome_config)
        try:
            driver.start()
            test_url = "https://httpbin.org/headers"
            driver.get(test_url)
            assert test_url in driver.current_url
            assert "httpbin" in driver.title.lower()
        finally:
            driver.stop()

    def test_javascript_execution(self, chrome_config):
        """Test JavaScript execution in the browser."""
        ChromeDriver = get_chrome_driver()
        driver = ChromeDriver(chrome_config)
        try:
            driver.start()
            result = driver.execute_script("return navigator.userAgent;")
            assert isinstance(result, str)
            assert "Chrome" in result
        finally:
            driver.stop()

    def test_browser_not_initialized(self, chrome_config):
        """Test that operations fail when browser is not initialized."""
        ChromeDriver = get_chrome_driver()
        driver = ChromeDriver(chrome_config)
        with pytest.raises(BrowserNotInitializedError):
            _ = driver.current_url
        with pytest.raises(BrowserNotInitializedError):
            _ = driver.title
        with pytest.raises(BrowserNotInitializedError):
            driver.get("https://example.com")

    def test_stop_browser(self, chrome_config):
        """Test that browser can be stopped properly."""
        ChromeDriver = get_chrome_driver()
        driver = ChromeDriver(chrome_config)
        driver.start()
        assert driver.is_running() is True
        
        driver.stop()
        assert driver.is_running() is False
        assert driver.driver is None

    def test_context_manager(self, chrome_config):
        """Test that the context manager works correctly."""
        ChromeDriver = get_chrome_driver()
        with ChromeDriver(config=chrome_config) as driver:
            assert driver.is_running() is True
            driver.get("https://httpbin.org/headers")
            assert "httpbin" in driver.title.lower()
        
        assert driver.is_running() is False

    def test_driver_configuration(self, chrome_config: ChromeConfig):
        """Test that driver configuration is applied correctly."""
        # Test headless mode
        chrome_config.headless = True
        with ChromeDriver(config=chrome_config) as driver:
            user_agent = driver.execute_script("return navigator.userAgent")
            assert "HeadlessChrome" in user_agent
        
        # Test window size
        chrome_config.headless = False
        chrome_config.window_size = (800, 600)
        with ChromeDriver(config=chrome_config) as driver:
            width = driver.execute_script("return window.innerWidth")
            height = driver.execute_script("return window.innerHeight")
            # Allow for browser chrome and potential DPI scaling
            assert 700 <= width <= 900
            assert 500 <= height <= 700
