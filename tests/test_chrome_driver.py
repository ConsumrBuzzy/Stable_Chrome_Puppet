"""Tests for the ChromeDriver implementation."""
import os
import sys
import time
import pytest
import logging
from pathlib import Path
from typing import Generator, Any, Dict

# Add parent directory to path to import our package
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from core.browser.drivers.chrome_driver import ChromeDriver
from core.browser.config import ChromeConfig, DriverConfig
from core.browser.exceptions import (
    BrowserError,
    BrowserNotInitializedError,
    NavigationError
)

# Mark all tests in this module as browser tests
pytestmark = [pytest.mark.browser, pytest.mark.driver]

class TestChromeDriver:
    """Test cases for ChromeDriver class."""
    
    @pytest.fixture
    def chrome_config(self) -> ChromeConfig:
        """Create a ChromeConfig fixture for testing."""
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
    def chrome_driver(self, chrome_config: ChromeConfig) -> Generator[ChromeDriver, None, None]:
        """Create and yield a ChromeDriver instance for testing."""
        driver = None
        try:
            driver = ChromeDriver(config=chrome_config)
            driver.start()
            yield driver
        finally:
            if driver:
                driver.stop()

    def test_initialization(self, chrome_driver: ChromeDriver):
        """Test that ChromeDriver initializes correctly."""
        assert chrome_driver is not None
        assert chrome_driver.is_running() is True
        assert chrome_driver.driver is not None

    def test_navigation(self, chrome_driver: ChromeDriver):
        """Test basic navigation functionality."""
        test_url = "https://httpbin.org/headers"
        chrome_driver.get(test_url)
        assert test_url in chrome_driver.current_url
        assert "httpbin" in chrome_driver.title.lower()

    def test_javascript_execution(self, chrome_driver: ChromeDriver):
        """Test JavaScript execution in the browser."""
        result = chrome_driver.execute_script("return navigator.userAgent;")
        assert isinstance(result, str)
        assert "Chrome" in result

    def test_browser_not_initialized(self, chrome_config: ChromeConfig):
        """Test that operations fail when browser is not initialized."""
        driver = ChromeDriver(config=chrome_config)
        with pytest.raises(BrowserNotInitializedError):
            _ = driver.current_url
        with pytest.raises(BrowserNotInitializedError):
            _ = driver.title
        with pytest.raises(BrowserNotInitializedError):
            driver.get("https://example.com")

    def test_stop_browser(self, chrome_config: ChromeConfig):
        """Test that browser can be stopped properly."""
        driver = ChromeDriver(config=chrome_config)
        driver.start()
        assert driver.is_running() is True
        
        driver.stop()
        assert driver.is_running() is False
        assert driver.driver is None

    def test_context_manager(self, chrome_config: ChromeConfig):
        """Test that the context manager works correctly."""
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
