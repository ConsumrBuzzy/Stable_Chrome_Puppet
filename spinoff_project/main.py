#!/usr/bin/env python3
"""
Stable Chrome Puppet - Core Browser Automation

A lightweight browser automation tool using Selenium WebDriver.
"""
import argparse
import logging
import sys
from typing import Optional, Tuple

from core.browser import ChromeBrowser
from core.config import ChromeConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Chrome browser automation tool')
    parser.add_argument('url', nargs='?', help='URL to open')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--timeout', type=int, default=30, help='Page load timeout in seconds')
    parser.add_argument('--window-size', type=str, default='1920,1080', 
                       help='Window size as WIDTH,HEIGHT (e.g., 1920,1080)')
    return parser.parse_args()

def main() -> int:
    """Main entry point for the script."""
    try:
        args = parse_arguments()
        
        # Configure Chrome options
        config = ChromeConfig(
            headless=args.headless,
            window_size=args.window_size,
            page_load_timeout=args.timeout
        )
        
        # Initialize browser
        with ChromeBrowser(config=config) as browser:
            if args.url:
                logger.info(f"Navigating to {args.url}")
                browser.get(args.url)
                logger.info(f"Page title: {browser.title}")
                
                # Keep the browser open for interaction if not in headless mode
                if not args.headless:
                    input("Press Enter to close the browser...")
        
        return 0
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
