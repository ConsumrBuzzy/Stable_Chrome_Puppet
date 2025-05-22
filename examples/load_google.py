"""
Simple script to load Google with a specific Chrome profile.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow importing from core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.browser.drivers.chrome.browser import ChromeBrowser
from core.browser.config import ChromeConfig

def get_default_chrome_user_data_dir() -> str:
    """Get the default Chrome user data directory based on OS."""
    if sys.platform.startswith('win'):
        return os.path.expandvars(r'%LOCALAPPDATA%\\Google\\Chrome\\User Data')
    elif sys.platform.startswith('darwin'):
        return os.path.expanduser('~/Library/Application Support/Google/Chrome')
    else:  # Linux and others
        return os.path.expanduser('~/.config/google-chrome')

def main():
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Load Google with a Chrome profile')
    parser.add_argument('--profile', type=str, default='Default',
                      help='Chrome profile name (e.g., "Profile 1", "Default")')
    parser.add_argument('--user-data-dir', type=str, default=None,
                      help=f'Custom Chrome user data directory (default: {get_default_chrome_user_data_dir()})')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Configure Chrome with profile settings
    config = ChromeConfig(
        headless=False,  # Show browser window
        user_data_dir=args.user_data_dir or get_default_chrome_user_data_dir(),
        profile_directory=args.profile,
        use_existing_profile=True,
        extra_args=[
            '--disable-notifications',
            '--start-maximized',
        ]
    )
    
    # Initialize and start browser
    browser = ChromeBrowser(config=config)
    
    try:
        logger.info(f"Starting browser with profile: {args.profile}")
        browser.start()
        
        # Navigate to Google
        browser.driver.get('https://www.google.com')
        logger.info("Browser started. Press Ctrl+C to exit.")
        
        # Keep browser open until interrupted
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        if 'browser' in locals():
            browser.stop()

if __name__ == "__main__":
    main()
