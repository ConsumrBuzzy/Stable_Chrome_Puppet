"""
Simplest possible Chrome browser example using Selenium.
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

def main():
    print("Starting Chrome browser...")
    
    # Basic Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # Start maximized
    
    try:
        # Try to create a Chrome instance with default settings
        driver = webdriver.Chrome(options=chrome_options)
        
        print("Navigating to Google...")
        driver.get("https://www.google.com")
        
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        print("Browser will remain open for 30 seconds...")
        time.sleep(30)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure Chrome is installed on your system")
        print("2. Install ChromeDriver that matches your Chrome version")
        print("   Download from: https://sites.google.com/chromium.org/driver/")
        print("3. Add ChromeDriver to your system PATH")
    finally:
        if 'driver' in locals():
            print("Closing the browser...")
            driver.quit()
        else:
            print("Could not start Chrome browser.")

if __name__ == "__main__":
    main()
