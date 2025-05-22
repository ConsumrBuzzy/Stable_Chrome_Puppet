"""Simple script to load Google.com using ChromeDriver."""
import sys
import time
from core.browser.browser import Browser
from core.browser.config import ChromeConfig

def main():
    # Configure Chrome with headless mode disabled
    config = ChromeConfig(
        headless=False,  # Set to True to run in headless mode
        window_size=(1200, 800),
        chrome_args=[
            '--disable-notifications',
            '--disable-infobars',
            '--disable-gpu',
            '--no-sandbox',
            '--disable-dev-shm-usage'
        ]
    )
    
    # Create and start the browser
    browser = Browser(config=config)
    
    try:
        # Start the browser
        print("Starting browser...")
        browser.start()
        
        # Navigate to Google
        print("Navigating to Google...")
        browser.navigate_to('https://www.google.com')
        
        # Get current URL and title
        print(f"Current URL: {browser.get_current_url()}")
        print(f"Page title: {browser.get_page_source()[:100]}...")  # Print first 100 chars of page source
        
        # Keep the browser open for a while
        print("Browser will close in 30 seconds...")
        time.sleep(30)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the browser
        print("Closing browser...")
        browser.stop()

if __name__ == "__main__":
    main()
