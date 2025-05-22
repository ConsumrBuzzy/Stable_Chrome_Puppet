"""
Simple script to load Google.com using ChromeDriver.

This script demonstrates basic browser automation with Chrome,
including proper error handling and resource cleanup.
"""
import sys
import time
import logging
from core.browser.browser import Browser
from core.browser.config import ChromeConfig
from core.browser.exceptions import BrowserError, NavigationError

def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('browser_automation.log')
        ]
    )

def main() -> None:
    """Run the browser automation example."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Configure Chrome with optimized settings
        config = ChromeConfig(
            headless=False,  # Set to True for headless mode
            window_size=(1200, 800),
            chrome_args=[
                # These are now handled by default in ChromeDriver
                # but can be overridden here if needed
            ]
        )
        
        logger.info("Initializing browser...")
        browser = Browser(config=config)
        
        try:
            # Start the browser
            logger.info("Starting browser...")
            browser.start()
            
            # Navigate to Google
            logger.info("Navigating to Google...")
            browser.navigate_to('https://www.google.com')
            
            # Get current URL and page info
            logger.info(f"Current URL: {browser.get_current_url()}")
            logger.info("Page loaded successfully")
            
            # Keep the browser open for a few seconds to see the result
            logger.info("Browser will close in 5 seconds...")
            time.sleep(5)
            
        except NavigationError as e:
            logger.error(f"Navigation failed: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        finally:
            # Ensure browser is always closed properly
            logger.info("Closing browser...")
            browser.stop()
            
    except BrowserError as e:
        logger.error(f"Browser initialization failed: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Script completed successfully")

if __name__ == "__main__":
    main()
