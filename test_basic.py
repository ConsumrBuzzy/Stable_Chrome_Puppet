"""Basic test script to verify Chrome automation setup."""
import sys
import logging
from pathlib import Path

# Add parent directory to path to import our package
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from chrome_puppet import ChromePuppet, ChromeConfig
from webdriver_manager.core.utils import ChromeType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_basic_navigation():
    """Test basic browser navigation and content retrieval."""
    config = ChromeConfig(
        headless=False,  # Set to True for headless mode
        window_size=(1400, 1000),
        chrome_type=ChromeType.GOOGLE,
        chrome_arguments=[
            "--disable-notifications",
            "--disable-infobars"
        ]
    )
    
    with ChromePuppet(config=config) as browser:
        try:
            # Test basic navigation
            browser.get("https://httpbin.org/headers")
            
            # Get page source as BeautifulSoup
            soup = browser.get_soup()
            if soup:
                print("\nPage title:", soup.title.text if soup.title else "No title found")
                
                # Print some content to verify
                pre_tags = soup.find_all('pre')
                if pre_tags:
                    print("\nResponse content (first 200 chars):")
                    print(str(pre_tags[0].text)[:200] + "...")
                else:
                    print("No <pre> tags found in the response")
            
            # Test JavaScript execution
            result = browser.driver.execute_script("return navigator.userAgent;")
            print(f"\nUser Agent: {result}")
            
            # Test taking a screenshot
            screenshot_path = "test_screenshot.png"
            browser.driver.save_screenshot(screenshot_path)
            print(f"\nScreenshot saved to: {screenshot_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)
            return False
        finally:
            if not config.headless:
                input("\nPress Enter to close the browser...")

if __name__ == "__main__":
    print("Starting Chrome Puppet test...")
    success = test_basic_navigation()
    print(f"\nTest {'passed' if success else 'failed'}")
    sys.exit(0 if success else 1)
