"""
Browser Automation Example
--------------------------
This example demonstrates how to use the Chrome Puppet for browser automation.
It includes basic navigation, element interaction, and cleanup.
"""
import time
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.browser.chrome import ChromeBrowser
from core.config import ChromeConfig

def main():
    """Run the browser automation example."""
    # Configure Chrome with common options
    config = ChromeConfig(
        headless=False,  # Set to True for headless mode
        window_size=(1280, 800),
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
    
    # Initialize the browser
    browser = None
    try:
        print("🚀 Starting Chrome browser...")
        browser = ChromeBrowser(config)
        browser.start()
        
        # Example: Navigate to Google
        print("🌐 Navigating to Google...")
        browser.navigate_to("https://www.google.com")
        print(f"   Current URL: {browser.get_current_url()}")
        print(f"   Page title: {browser.driver.title}")
        
        # Example: Interact with elements
        search_box = browser.find_element("name", "q")
        if search_box:
            search_box.send_keys("Chrome Puppet")
            search_box.submit()
            time.sleep(2)  # Wait for results
            
            # Example: Take a screenshot
            print("📸 Taking a screenshot...")
            screenshot_path = "google_search_results.png"
            browser.take_screenshot(screenshot_path)
            print(f"   Screenshot saved to: {screenshot_path}")
        
        print("✅ Example completed successfully!")
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        raise
    finally:
        # Always clean up
        if browser:
            print("🛑 Closing browser...")
            browser.stop()

if __name__ == "__main__":
    main()
