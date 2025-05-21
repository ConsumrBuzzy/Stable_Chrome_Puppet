"""Pytest configuration and fixtures."""
import os
import sys
import time
import socket
import threading
import http.server
import socketserver
from pathlib import Path
from typing import Generator, Optional, Tuple

import pytest

# Add parent directory to path to import our package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from core.config import ChromeConfig
from core.browser.chrome import ChromeBrowser

# Set up test directories
TEST_DIR = Path(__file__).parent
SCREENSHOT_DIR = TEST_DIR / "screenshots"
TEST_DATA_DIR = TEST_DIR / "test_data"

# Ensure test directories exist
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(TEST_DATA_DIR, exist_ok=True)

# Test server configuration
TEST_HOST = "127.0.0.1"
TEST_PORT = 8000
TEST_BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}"

@pytest.fixture(scope="session")
def chrome_config() -> ChromeConfig:
    """Create a ChromeConfig for testing."""
    return ChromeConfig(
        headless=True,  # Run in headless mode for CI
        window_size=(1280, 1024),
        implicit_wait=10,
        screenshot_dir=str(SCREENSHOT_DIR),
    )

@pytest.fixture
def browser(chrome_config: ChromeConfig) -> Generator[ChromeBrowser, None, None]:
    """Create a Chrome browser instance for testing."""
    browser = ChromeBrowser(chrome_config)
    browser.start()
    try:
        yield browser
    finally:
        browser.stop()

@pytest.fixture
def test_page_url() -> str:
    """Return the URL to a test page."""
    # In a real test, this would point to a local test server or test page
    return "https://example.com"

# Add command line options
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--headful",
        action="store_true",
        default=False,
        help="Run tests in headful mode (shows browser)",
    )
    parser.addoption(
        "--slow",
        action="store_true",
        default=False,
        help="Run slow tests",
    )

class TestServer:
    """Simple HTTP server for serving test files."""
    
    def __init__(self, host: str, port: int, directory: Path):
        self.host = host
        self.port = port
        self.directory = directory
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the test server in a separate thread."""
        os.chdir(str(self.directory))
        handler = http.server.SimpleHTTPRequestHandler
        self.server = socketserver.TCPServer((self.host, self.port), handler, bind_and_activate=False)
        
        # Allow address reuse
        self.server.allow_reuse_address = True
        
        # Try to bind to the port, handling the case where it's already in use
        for attempt in range(5):
            try:
                self.server.server_bind()
                self.server.server_activate()
                break
            except OSError as e:
                if "Address already in use" in str(e) and attempt < 4:
                    time.sleep(1)
                    continue
                raise
        
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the test server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.thread:
                self.thread.join(timeout=1)
        self.server = None
        self.thread = None

@pytest.fixture(scope="session")
def test_server():
    """Start a test server for serving test pages."""
    server = TestServer(
        host=TEST_HOST,
        port=TEST_PORT,
        directory=TEST_DATA_DIR
    )
    
    server.start()
    
    # Wait for server to start
    max_attempts = 10
    for _ in range(max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex((TEST_HOST, TEST_PORT)) == 0:
                    break
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)
    else:
        raise RuntimeError("Test server failed to start")
    
    yield server
    
    server.stop()

@pytest.fixture
def test_page_url(test_server) -> str:
    """Return the URL to the test page."""
    return f"{TEST_BASE_URL}/test_page.html"

@pytest.fixture
def test_page_with_form(test_server) -> str:
    """Return the URL to the test page with form elements."""
    return f"{TEST_BASE_URL}/test_page.html"

# Configure logging for tests
@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests."""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Disable logging for selenium.webdriver.remote.remote_connection
    # to reduce noise in test output
    logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
