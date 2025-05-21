#!/usr/bin/env python3
"""
Chrome Puppet - A robust Chrome browser automation tool.

This script provides a command-line interface to load and interact with web pages
using the ChromePuppet automation framework.
"""
import argparse
import logging
import sys
import os
from pathlib import Path

# Fix Windows console encoding for emoji support
if os.name == 'nt':
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Import after path setup
from core.orchestrator import ChromePuppetOrchestrator, create_orchestrator
from core.config import ChromeConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('chrome_puppet.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def load_url(url, headless=False, wait_time=10):
    """
    Load a URL in Chrome and return the page information.
    
    Args:
        url (str): The URL to load
        headless (bool): Whether to run in headless mode
        wait_time (int): Time in seconds to wait for page load
        
    Returns:
        dict: Dictionary containing page information or error message
    """
    # Set up logging
    logger.info(f"🚀 Loading URL: {url}")
    logger.info(f"   Headless: {headless}")
    logger.info(f"   Wait time: {wait_time} seconds")
    
    config = ChromeConfig(
        headless=headless,
        window_size=(1920, 1080),
        implicit_wait=wait_time,
        chrome_arguments=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-extensions',
            '--remote-debugging-port=9222'
        ]
    )
    
    orchestrator = None
    try:
        orchestrator = create_orchestrator(config=config)
        orchestrator.start_browser()
        if orchestrator.browser:
            orchestrator.browser.get(url)
            
            result = {
                'success': True,
                'url': url,
                'title': orchestrator.browser.driver.title,
                'current_url': orchestrator.browser.driver.current_url,
                'page_source': orchestrator.browser.driver.page_source[:1000] + '...'  # First 1000 chars
            }
            return result
    except Exception as e:
        logger.error(f"Error loading URL {url}: {e}")
        return {
            'success': False,
            'url': url,
            'error': str(e)
        }
    finally:
        if orchestrator:
            try:
                orchestrator.stop_browser()
            except Exception as e:
                logger.error(f"Error stopping browser: {e}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Chrome Puppet - Browser Automation Tool')
    parser.add_argument('url', nargs='?', default='https://www.google.com', 
                      help='URL to load (default: https://www.google.com)')
    parser.add_argument('--headless', action='store_true', 
                      help='Run in headless mode')
    parser.add_argument('--visible', dest='headless', action='store_false', 
                      help='Run in visible mode')
    parser.add_argument('--wait', type=int, default=10, 
                      help='Wait time in seconds (default: 10)')
    return parser.parse_args()


def main():
    """Main entry point for the Chrome Puppet CLI."""
    args = parse_arguments()
    
    print(f"🚀 Chrome Puppet - Loading URL: {args.url}")
    print(f"   Headless: {args.headless}")
    print(f"   Wait time: {args.wait} seconds")
    
    result = load_url(
        url=args.url,
        headless=args.headless,
        wait_time=args.wait
    )
    
    if result['success']:
        print("\n✅ Page loaded successfully!")
        print(f"   Title: {result['title']}")
        print(f"   Final URL: {result['url']}")
        print("\n📄 Page source preview:")
        print("-" * 50)
        print(result['page_source'])
        print("-" * 50)
        print("\n✅ Done! Check chrome_puppet.log for detailed logs.")
    else:
        print(f"\n❌ Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()

    # Initialize the browser (headless by default)
    # To run with a visible browser, set headless=False
    browser_base = None
    try:
        browser_base = ChromeWebDriverBase(headless=True)
        # browser_base = ChromeWebDriverBase(headless=False) # To see the browser in action

        if browser_base.driver: # Check if driver initialized successfully
            # Get BeautifulSoup object directly
            soup = browser_base.get_soup(test_url, wait_time=5)

            if soup:
                print(f"\nSuccessfully retrieved and parsed content from: {test_url}")
                # Example: Extract all quotes (these are in <span class="text"> elements)
                quotes = soup.find_all('span', class_='text')
                if quotes:
                    print(f"\nFound {len(quotes)} quotes:")
                    for i, quote in enumerate(quotes):
                        print(f"{i+1}. {quote.get_text(strip=True)}")
                else:
                    print("No quotes found with the specified selector.")

                # Example: Extract all author names
                authors = soup.find_all('small', class_='author')
                if authors:
                    print(f"\nFound {len(authors)} authors:")
                    for author in authors:
                        print(f"- {author.get_text(strip=True)}")
                else:
                    print("No authors found.")
            else:
                print(f"Could not retrieve soup object from {test_url}")
        else:
            print("Browser base could not be initialized. Exiting.")

    except Exception as e:
        print(f"An error occurred during the main execution: {e}")
    finally:
        if browser_base:
            browser_base.close_driver()