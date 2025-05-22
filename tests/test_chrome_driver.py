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
from core.browser.drivers.chrome_driver import ChromeDriver
from core.browser.driver_config import DriverConfig

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
    def chrome_driver(self, chrome_config) -> 'Generator[ChromeDriver, None, None]':
        """Create and yield a ChromeDriver instance for testing."""
        driver = ChromeDriver(chrome_config)
        try:
            driver.start()
            yield driver
        finally:
            driver.stop()

    def test_initialization(self, chrome_config):
        """Test that ChromeDriver initializes correctly."""
        driver = ChromeDriver(chrome_config)
        try:
            assert driver is not None
            driver.start()
            assert driver.driver is not None
            assert driver.config == chrome_config
        finally:
            driver.stop()

    def test_navigation(self, chrome_config):
        """Test basic navigation functionality."""
        driver = ChromeDriver(chrome_config)
        try:
            driver.start()
            test_url = "https://httpbin.org/headers"
            driver.navigate_to(test_url)
            current_url = driver.get_current_url()
            assert test_url in current_url
            page_source = driver.get_page_source()
            assert "httpbin" in page_source.lower()
        finally:
            driver.stop()

    def test_javascript_execution(self, chrome_config):
        """Test JavaScript execution in the browser."""
        driver = ChromeDriver(chrome_config)
        try:
            driver.start()
            # Execute JavaScript to get browser info
            user_agent = driver.driver.execute_script("return navigator.userAgent;")
            assert isinstance(user_agent, str)
            assert "Chrome" in user_agent
            
            # Test a simple calculation
            result = driver.driver.execute_script("return 2 + 2;")
            assert result == 4
        finally:
            driver.stop()

    def test_browser_not_initialized(self, chrome_config):
        """Test that operations fail when browser is not initialized."""
        driver = ChromeDriver(chrome_config)
        # Don't call start() - browser should not be initialized
        with pytest.raises(BrowserNotInitializedError):
            _ = driver.current_url
        with pytest.raises(BrowserNotInitializedError):
            _ = driver.title
        with pytest.raises(BrowserNotInitializedError):
            driver.get("https://example.com")

    def test_stop_browser(self, chrome_config):
        """Test that browser can be stopped properly."""
        driver = ChromeDriver(chrome_config)
        driver.start()  # Start the browser first
        driver.start()
        assert driver.is_running() is True
        
        driver.stop()
        assert driver.is_running() is False
        assert driver.driver is None

    def test_context_manager(self, chrome_config):
        """Test that the context manager works correctly."""
        with ChromeDriver(chrome_config) as driver:
            assert driver.is_running() is True
            driver.navigate_to("https://httpbin.org/headers")
            page_source = driver.get_page_source()
            assert "httpbin" in page_source.lower()
        
        assert driver.is_running() is False

    def test_driver_configuration(self, chrome_config: ChromeConfig):
        """Test that driver configuration is applied correctly."""
        # Test headless mode
        chrome_config.headless = True
        driver = ChromeDriver(config=chrome_config)
        try:
            driver.start()
            # Test that the browser is running in headless mode
            assert driver.driver is not None
            
            # Test navigation in headless mode
            test_url = "https://httpbin.org/headers"
            driver.navigate_to(test_url)
            current_url = driver.get_current_url()
            assert test_url in current_url
            
            # Verify headless mode
            user_agent = driver.driver.execute_script("return navigator.userAgent")
            assert "HeadlessChrome" in user_agent
        finally:
            driver.stop()
        
        # Test window size
        chrome_config.headless = False
        chrome_config.window_size = (800, 600)
        with ChromeDriver(config=chrome_config) as driver:
            width = driver.execute_script("return window.innerWidth")
            height = driver.execute_script("return window.innerHeight")
            # Allow for browser chrome and potential DPI scaling
            assert 700 <= width <= 900
            assert 500 <= height <= 700
