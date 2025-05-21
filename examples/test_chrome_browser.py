"""
Test script for Chrome browser implementation.

This script demonstrates the core functionality of the Chrome browser implementation.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow importing from core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import ChromePuppet, ChromeConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_browser():
    """Test Chrome browser functionality using ChromePuppet."""
    # Configure Chrome
    config = ChromeConfig(
        headless=False,  # Set to True for headless mode
        window_size=(1200, 800),
        chrome_arguments=[
            "--disable-notifications",
            "--disable-extensions"
        ]
    )
    
    # Initialize ChromePuppet
    puppet = None
    try:
        logger.info("Initializing ChromePuppet...")
        puppet = ChromePuppet(config)
        
        # Start the browser
        logger.info("Starting browser...")
        puppet.start()
        
        # Test navigation
        logger.info("Navigating to Google...")
        puppet.navigate_to("https://www.google.com")
        
        # Get page info
        current_url = puppet.get_current_url()
        logger.info(f"Current URL: {current_url}")
        
        # Get page source (first 200 chars)
        page_source = puppet.get_page_source()
        logger.info(f"Page source preview: {page_source[:200]}...")
        
        # Take a screenshot
        screenshot_path = "screenshot.png"
        if puppet.take_screenshot(screenshot_path):
            logger.info(f"Screenshot saved to: {os.path.abspath(screenshot_path)}")
        
        # Execute some JavaScript
        title = puppet.execute_script("return document.title")
        logger.info(f"Page title: {title}")
        
        logger.info("Test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False
    finally:
        # Clean up
        if puppet and puppet.is_running:
            logger.info("Stopping browser...")
            puppet.stop()

if __name__ == "__main__":
    if test_browser():
        logger.info("All tests passed!")
        sys.exit(0)
    else:
        logger.error("Tests failed!")
        sys.exit(1)
