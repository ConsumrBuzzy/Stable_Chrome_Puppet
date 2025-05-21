"""Tests for the Chrome browser implementation."""
import sys
from pathlib import Path

# Add parent directory to path to import our package
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

import pytest
import time
from typing import Generator

from core.browser.exceptions import BrowserError, NavigationError
from core.config import ChromeConfig

# Mark all tests in this module as browser tests
pytestmark = [pytest.mark.browser]

class TestChromeBrowser:
    """Test cases for ChromeBrowser class."""
    
    def test_browser_initialization(self, browser):
        """Test that the browser initializes correctly."""
        assert browser.is_running()
        assert browser.driver is not None
        assert "data" in browser.driver.capabilities
    
    def test_navigation(self, browser, test_page_url):
        """Test basic navigation to a URL."""
        browser.get(test_page_url)
        assert "Example Domain" in browser.driver.title
    
    def test_page_source(self, browser, test_page_url):
        """Test retrieving page source."""
        browser.get(test_page_url)
        page_source = browser.get_page_source()
        assert isinstance(page_source, str)
        assert len(page_source) > 0
        assert "Example Domain" in page_source
    
    def test_current_url(self, browser, test_page_url):
        """Test getting the current URL."""
        browser.get(test_page_url)
        current_url = browser.get_current_url()
        assert current_url == test_page_url
    
    def test_take_screenshot(self, browser, test_page_url, tmp_path):
        """Test taking a screenshot."""
        browser.get(test_page_url)
        screenshot_path = tmp_path / "screenshot.png"
        result = browser.screenshot.take_screenshot(str(screenshot_path))
        
        assert result is True
        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 0
    
    def test_invalid_url_raises_error(self, browser):
        """Test that navigating to an invalid URL raises an error."""
        with pytest.raises(NavigationError):
            browser.get("http://thisurldoesnotexist.xyz")
    
    def test_browser_restart(self, browser):
        """Test that the browser can be stopped and restarted."""
        # First session
        browser.get("https://example.com")
        assert "Example" in browser.driver.title
        
        # Restart
        browser.stop()
        assert not browser.is_running()
        
        # Second session
        browser.start()
        browser.get("https://example.org")
        assert "Example" in browser.driver.title

class TestChromeConfig:
    """Test cases for ChromeConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ChromeConfig()
        assert config.headless is False
        assert config.window_size == (1366, 768)
        assert config.implicit_wait == 30
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = ChromeConfig(
            headless=True,
            window_size=(1920, 1080),
            implicit_wait=10,
            chrome_arguments=["--disable-extensions"]
        )
        assert config.headless is True
        assert config.window_size == (1920, 1080)
        assert config.implicit_wait == 10
        assert "--disable-extensions" in config.chrome_arguments

@pytest.mark.slow
def test_parallel_browser_instances():
    """Test that multiple browser instances can run in parallel."""
    config = ChromeConfig(headless=True)
    browsers = []
    
    try:
        # Create multiple browser instances
        for i in range(3):
            browser = ChromeBrowser(config)
            browser.start()
            browser.get(f"https://example.com?test={i}")
            browsers.append(browser)
        
        # Verify all browsers are running
        for i, browser in enumerate(browsers):
            assert browser.is_running()
            assert f"test={i}" in browser.get_current_url()
    finally:
        # Clean up
        for browser in browsers:
            browser.stop()
