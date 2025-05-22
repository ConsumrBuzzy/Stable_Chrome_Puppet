"""Simple script to test loading Google.com using ChromeDriver."""
import sys
import time
import logging
from core.browser.drivers.chrome_driver import ChromeDriver
from core.browser.config import ChromeConfig, DriverConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to test loading Google.com."""
    # Configure Chrome
    config = ChromeConfig(
        headless=False,  # Set to True to run in headless mode
        window_size=(1200, 800),
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
    
    # Create ChromeDriver instance
    browser = ChromeDriver(config=config, logger=logger)
    
    try:
        # Start the browser
        logger.info("Starting Chrome browser...")
        browser.start()
        
        # Navigate to Google
        logger.info("Navigating to Google...")
        browser.navigate_to('https://www.google.com')
        
        # Get current URL and page source
        logger.info(f"Current URL: {browser.get_current_url()}")
        logger.info(f"Page source length: {len(browser.get_page_source())} characters")
        
        # Keep the browser open for a while
        logger.info("Browser will close in 30 seconds...")
        time.sleep(30)
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        # Close the browser
        logger.info("Closing browser...")
        browser.stop()

if __name__ == "__main__":
    main()
