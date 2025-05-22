"""
Simple script to load Google.com using ChromeDriver with profile support.

This script demonstrates browser automation with Chrome, including:
- Using existing Chrome profiles
- Enabling password manager
- Proper error handling and resource cleanup
"""
import sys
import os
import logging
import platform
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from core.browser import ChromeBrowser
from core.browser.config import ChromeConfig
from core.browser.exceptions import BrowserError, NavigationError

def get_default_chrome_user_data_path() -> str:
    """Get the default Chrome user data directory path based on the OS."""
    system = platform.system().lower()
    if system == 'windows':
        return os.path.expandvars(r'%LOCALAPPDATA%\\Google\\Chrome\\User Data')
    elif system == 'darwin':  # macOS
        return str(Path.home() / 'Library/Application Support/Google/Chrome')
    else:  # Linux
        return str(Path.home() / '.config/google-chrome')

def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.
    
    Args:
        verbose: If True, set log level to DEBUG
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('browser_automation.log')
        ]
    )

def main() -> None:
    """Run the browser automation example with profile support."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Load Google with Chrome profile')
    parser.add_argument('--profile', type=str, default='Default',
                       help='Chrome profile name (e.g., "Profile 1", "Default")')
    parser.add_argument('--user-data-dir', type=str, default=None,
                       help=f'Custom Chrome user data directory (default: {get_default_chrome_user_data_path()})')
    parser.add_argument('--headless', action='store_true',
                       help='Run in headless mode')
    parser.add_argument('--no-password-manager', action='store_false', dest='password_manager',
                       help='Disable password manager')
    parser.add_argument('--no-prompts', action='store_false', dest='prompts',
                       help='Disable password manager prompts')
    parser.add_argument('--url', type=str, default='https://www.google.com',
                       help='URL to navigate to (default: https://www.google.com)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)
    
    # Determine the user data directory
    user_data_dir = args.user_data_dir or get_default_chrome_user_data_path()
    
    logger.info(f"Using Chrome profile: {args.profile}")
    logger.debug(f"User data directory: {user_data_dir}")
    
    try:
        # Configure Chrome with profile settings
        config = ChromeConfig(
            headless=args.headless,
            window_size=(1200, 800),
            user_data_dir=user_data_dir,
            profile_directory=args.profile,
            use_existing_profile=True,
            extra_args=[
                # Additional Chrome arguments can be added here
                '--disable-notifications',
                '--disable-infobars',
            ]
        )
        
        logger.info("Initializing browser with profile...")
        browser = ChromeBrowser(config=config)
        
        try:
            # Start the browser
            logger.info("Starting browser...")
            browser.start()
            
            # Navigate to the specified URL
            logger.info(f"Navigating to {args.url}...")
            browser.driver.get(args.url)
            
            # Get current URL and page info
            current_url = browser.driver.current_url
            logger.info(f"Current URL: {current_url}")
            logger.info("Page loaded successfully")
            
            # Take a screenshot
            screenshot_file = 'screenshot.png'
            logger.info(f"Taking screenshot: {screenshot_file}")
            browser.driver.save_screenshot(screenshot_file)
            
            # Keep the browser open for a few seconds to see the result
            logger.info("Browser will close in 5 seconds...")
            time.sleep(5)
            
        except NavigationError as e:
            logger.error(f"Navigation failed: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        finally:
            # Ensure browser is always closed properly
            logger.info("Closing browser...")
            browser.stop()
            
    except BrowserError as e:
        logger.error(f"Browser initialization failed: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Script completed successfully")

if __name__ == "__main__":
    main()
