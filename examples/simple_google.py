"""
Simple example to open Chrome and navigate to Google.com using Selenium directly.
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
from pathlib import Path

def main():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Get the path to ChromeDriver (assuming it's in the project root)
    project_root = Path(__file__).parent.parent
    chromedriver_path = project_root / 'chromedriver.exe'
    
    if not chromedriver_path.exists():
        print("ChromeDriver not found. Please download it and place it in the project root.")
        print(f"Expected path: {chromedriver_path}")
        return
    
    # Initialize the Chrome WebDriver
    print("Starting Chrome browser...")
    service = Service(executable_path=str(chromedriver_path))
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
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
