"""
Simple example to demonstrate launching a headed Chrome browser and navigating to Google.com.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.config import ChromeConfig
from core.browser.chrome import ChromeBrowser

def main():
    # Configure Chrome to run in headed mode
    config = ChromeConfig(
        headless=False,  # Run in headed mode
        window_size=(1280, 1024),
        implicit_wait=10,
        chrome_arguments=[
            "--disable-notifications",
            "--disable-infobars",
            "--disable-extensions",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]
    )
    
    # Create and start the browser
    browser = ChromeBrowser(config)
    
    try:
        print("Starting Chrome browser...")
        browser.start()
        
        # Navigate to Google
        print("Navigating to Google...")
        browser.navigate_to("https://www.google.com")
        
        print(f"Current URL: {browser.get_current_url()}")
        print(f"Page title: {browser.driver.title}")
        
        # Keep the browser open for 30 seconds so you can see it
        print("Browser will remain open for 30 seconds...")
        import time
        time.sleep(30)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Make sure to close the browser when done
        print("Closing the browser...")
        browser.stop()

if __name__ == "__main__":
    main()
