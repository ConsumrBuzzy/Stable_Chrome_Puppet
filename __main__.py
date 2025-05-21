#!/usr/bin/env python3
"""
Chrome Puppet - A robust and extensible Chrome browser automation tool.

This is the main entry point for the Chrome Puppet package.
"""

import argparse
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Chrome Puppet - A robust Chrome browser automation tool.'
    )
    
    # Add common arguments
    parser.add_argument(
        '--version',
        action='store_true',
        help='show version information and exit'
    )
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='command to execute')
    
    # Run tests command
    test_parser = subparsers.add_parser('test', help='run tests')
    test_parser.add_argument(
        'test_name',
        nargs='?',
        help='specific test to run (optional)'
    )
    
    # Run browser command
    browser_parser = subparsers.add_parser('browser', help='launch browser')
    browser_parser.add_argument(
        '--headless',
        action='store_true',
        help='run in headless mode'
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the Chrome Puppet CLI."""
    import os
    
    # Suppress TensorFlow Lite XNNPACK delegate warnings
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=INFO, 1=WARNING, 2=ERROR, 3=FATAL
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable oneDNN optimizations
    
    args = parse_args()
    
    if args.version:
        from core import __version__
        print(f"Chrome Puppet v{__version__}")
        return 0
    
    if args.command == 'test':
        # Run tests
        import unittest
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover('tests')
        test_runner = unittest.TextTestRunner(verbosity=2)
        result = test_runner.run(test_suite)
        return 0 if result.wasSuccessful() else 1
    
    elif args.command == 'browser':
        # Launch browser
        from core.browser.chrome import ChromeBrowser
        from core.config import ChromeConfig
        from core.utils import signal_handling
        import time
        
        try:
            # Get URL from user
            url = input("Enter URL to load (e.g., https://example.com): ").strip()
            if not url:
                print("No URL provided. Using default: https://example.com")
                url = "https://example.com"
                
            # Ensure URL has a scheme
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            print(f"\nLaunching Chrome browser (headed mode) to load: {url}")
            
            # Configure browser (force headed mode)
            config = ChromeConfig(
                headless=False,  # Force headed mode
                window_size=(1366, 768),
                verbose=True
            )
            
            # Initialize browser
            browser = ChromeBrowser(config=config)
            browser_instance = browser  # Store globally for signal handler
            
            try:
                # Start browser and navigate to URL
                print("Starting browser...")
                browser.start()
                print(f"Navigating to {url}...")
                browser.navigate_to(url)
                
                # Display page info
                print(f"\nPage loaded successfully!")
                print(f"Title: {browser.driver.title}")
                print(f"URL: {browser.get_current_url()}")
                print("\nBrowser will close automatically in 30 seconds...")
                print("Press Ctrl+C to close immediately")
                
                    # Wait for 30 seconds or until interrupted
                    print("\nBrowser will close automatically in 30 seconds...")
                    print("Press Ctrl+C to close immediately")
                    
                    start_time = time.time()
                    while time.time() - start_time < 30:
                        time.sleep(0.5)  # Shorter sleep for better responsiveness
                        
                except KeyboardInterrupt:
                    print("\nInterrupted by user.")
                except Exception as e:
                    print(f"\nError: {e}")
                    time.sleep(2)  # Give user a moment to see the error
                finally:
                    if browser.is_running():
                        print("\nShutting down browser...")
                        browser.stop()
                        print("Browser closed.")
            
            except Exception as e:
                print(f"\nFatal error: {e}")
                return 1
            
        return 0
    
    else:
        print("Please specify a command. Use --help for more information.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
