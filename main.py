#!/usr/bin/env python3
"""
Stable Chrome Puppet - A reliable browser automation tool.

This script provides a command-line interface to control Chrome browser automation.
It can be used to load URLs, take screenshots, and perform other browser actions.

Usage:
    python main.py [URL] [options]

Examples:
    python main.py https://www.google.com
    python main.py https://www.example.com --headless --timeout 10 --screenshot
"""
import argparse
import logging
import re
import sys
import time
from typing import Optional, Tuple
from urllib.parse import urlparse

from core.browser import Browser, ChromeBrowser
from core.browser.config import ChromeConfig
from core.browser.exceptions import BrowserError, NavigationError


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL.
    
    Args:
        url: The URL to validate
        
    Returns:
        bool: True if the URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except (ValueError, AttributeError):
        return False


def prompt_for_url() -> str:
    """Prompt the user to enter a URL.
    
    Returns:
        str: The URL entered by the user or the default Google URL
    """
    default_url = 'https://www.google.com'
    prompt = f"Enter URL to load [default: {default_url}]: "
    
    while True:
        try:
            user_input = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nUsing default URL.")
            return default_url
            
        if not user_input:  # User pressed Enter
            return default_url
            
        # Add https:// if no scheme is provided
        if not user_input.startswith(('http://', 'https://')):
            user_input = f'https://{user_input}'
            
        if is_valid_url(user_input):
            return user_input
            
        print("Invalid URL. Please try again (e.g., example.com or https://example.com)")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('browser_automation.log')
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments
    """
    parser = argparse.ArgumentParser(
        description='Stable Chrome Puppet - A reliable browser automation tool.'
    )
    
    parser.add_argument(
        'url',
        nargs='?',
        default=None,
        help='URL to load (prompt if not provided)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode (no GUI)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Time in seconds to keep the browser open (default: 30)'
    )
    parser.add_argument(
        '--window-size',
        type=str,
        default='1200,800',
        help='Window size as WIDTH,HEIGHT (default: 1200,800)'
    )
    parser.add_argument(
        '--screenshot',
        action='store_true',
        help='Take a screenshot before closing the browser'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def parse_window_size(size_str: str) -> Tuple[int, int]:
    """Parse window size string into width and height.
    
    Args:
        size_str: Window size as 'WIDTH,HEIGHT' string
        
    Returns:
        Tuple of (width, height)
        
    Raises:
        ValueError: If the size string is invalid
    """
    try:
        width, height = map(int, size_str.split(','))
        if width <= 0 or height <= 0:
            raise ValueError("Window dimensions must be positive integers")
        return width, height
    except (ValueError, AttributeError) as e:
        logger.error(f"Invalid window size format: {size_str}. Using default 1200x800.")
        return 1200, 800


def main() -> int:
    """Main entry point for the script.
    
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    args = parse_arguments()
    
    # If no URL provided as argument, prompt the user
    if args.url is None:
        args.url = prompt_for_url()
    # Validate the provided URL
    elif not is_valid_url(args.url):
        print(f"Warning: '{args.url}' is not a valid URL. Defaulting to Google.")
        args.url = 'https://www.google.com'
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Parse window size
        window_size = parse_window_size(args.window_size)
        
        # Configure Chrome
        config = ChromeConfig(
            headless=args.headless,
            window_size=window_size,
            chrome_args=[
                '--disable-notifications',
                '--disable-infobars',
            ]
        )
        
        logger.info(f"Initializing Chrome browser (headless={args.headless})...")
        browser = Browser(config=config)
        
        try:
            # Start the browser
            logger.info("Starting browser...")
            browser.start()
            
            # Navigate to the URL
            logger.info(f"Navigating to {args.url}...")
            browser.navigate_to(args.url)
            
            # Get page information
            current_url = browser.get_current_url()
            logger.info(f"Current URL: {current_url}")
            
            if args.screenshot:
                screenshot_file = 'screenshot.png'
                logger.info(f"Taking screenshot: {screenshot_file}")
                browser.take_screenshot(screenshot_file)
            
            # Keep the browser open for the specified duration
            logger.info(f"Browser will close in {args.timeout} seconds...")
            time.sleep(args.timeout)
            
        except NavigationError as e:
            logger.error(f"Navigation failed: {e}")
            return 1
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            return 1
        finally:
            # Ensure browser is always closed properly
            logger.info("Closing browser...")
            browser.stop()
            
    except BrowserError as e:
        logger.error(f"Browser initialization failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return 1
    
    logger.info("Script completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
