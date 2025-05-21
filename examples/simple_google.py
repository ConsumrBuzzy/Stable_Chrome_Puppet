"""
Simple example to open Chrome and navigate to Google.com using Selenium directly.
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

def main():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize the Chrome WebDriver
    print("Starting Chrome browser...")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    try:
        # Navigate to Google
        print("Navigating to Google...")
        driver.get("https://www.google.com")
        
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Keep the browser open for 30 seconds
        print("Browser will remain open for 30 seconds...")
        time.sleep(30)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Make sure to close the browser when done
        print("Closing the browser...")
        driver.quit()

if __name__ == "__main__":
    main()
