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
        # Launch browser using the site handler system
        from core.sites import get_site_handler, register_site_handler
        from core.sites.example_site import ExampleSiteHandler
        from core.config import ChromeConfig
        from core.utils import signal_handling
        import time
        import json
        from pathlib import Path
        
        # Register our example site handler
        register_site_handler('example', ExampleSiteHandler)
        
        # Get site handler
        site_name = input("Enter site name (or 'custom' for direct URL): ").strip().lower()
        
        if site_name == 'custom':
            # Use direct URL mode
            url = input("Enter URL to load: ").strip()
            if not url:
                print("No URL provided. Using default: https://example.com")
                url = "https://example.com"
                
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            print(f"\nLaunching Chrome browser to load: {url}")
            
            # Configure browser
            config = ChromeConfig(
                headless=False,
                window_size=(1366, 768),
                verbose=True
            )
            
            # Use the browser directly
            with signal_handling():
                browser = ChromeBrowser(config=config)
                
                def cleanup():
                    if hasattr(browser, 'is_running') and browser.is_running():
                        print("\nCleaning up browser...")
                        browser.stop()
                
                signal_handling(cleanup)
                
                try:
                    print("Starting browser...")
                    browser.start()
                    print(f"Navigating to {url}...")
                    browser.navigate_to(url)
                    
                    print(f"\nPage loaded successfully!")
                    print(f"Title: {browser.driver.title}")
                    print(f"URL: {browser.get_current_url()}")
                    
                    print("\nBrowser will close automatically in 30 seconds...")
                    print("Press Ctrl+C to close immediately")
                    
                    start_time = time.time()
                    while time.time() - start_time < 30:
                        time.sleep(0.5)
                        
                except KeyboardInterrupt:
                    print("\nInterrupted by user.")
                except Exception as e:
                    print(f"\nError: {e}")
                    time.sleep(2)
                finally:
                    if hasattr(browser, 'is_running') and browser.is_running():
                        print("\nShutting down browser...")
                        browser.stop()
                        print("Browser closed.")
        else:
            # Use site handler mode
            site_handler_class = get_site_handler(site_name)
            if not site_handler_class:
                print(f"\nError: No handler found for site '{site_name}'")
                print("Available sites:")
                for name in ['example']:  # Add more as they become available
                    print(f"  - {name}")
                return 1
                
            print(f"\nLaunching {site_name} handler...")
            
            # Configure browser
            config = ChromeConfig(
                headless=False,
                window_size=(1366, 768),
                verbose=True
            )
            
            # Create data directory
            data_dir = Path.cwd() / 'data' / site_name
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Use the site handler
            with signal_handling():
                site = site_handler_class(config=config, data_dir=data_dir)
                
                def cleanup():
                    if hasattr(site, 'browser') and site.browser and site.browser.is_running():
                        print("\nCleaning up site handler...")
                        site.stop_browser()
                
                signal_handling(cleanup)
                
                try:
                    # Example: Login flow
                    if not site.is_logged_in():
                        print("You need to log in first.")
                        username = input("Username: ")
                        password = input("Password: ")
                        
                        print("Logging in...")
                        if site.login(username, password):
                            print("Login successful!")
                            site.save_cookies()  # Save cookies for future sessions
                        else:
                            print("Login failed!")
                            return 1
                    else:
                        print("Already logged in!")
                    
                    # Example: Do something with the site
                    print("\nFetching dashboard data...")
                    try:
                        dashboard_data = site.get_dashboard_data()
                        print("\nDashboard data:")
                        print(json.dumps(dashboard_data, indent=2))
                    except NotImplementedError:
                        print("Dashboard data not implemented for this site")
                    
                    # Keep the browser open for a while
                    print("\nBrowser will close automatically in 30 seconds...")
                    print("Press Ctrl+C to close immediately")
                    
                    start_time = time.time()
                    while time.time() - start_time < 30:
                        time.sleep(0.5)
                        
                except KeyboardInterrupt:
                    print("\nInterrupted by user.")
                except Exception as e:
                    print(f"\nError: {e}")
                    time.sleep(2)
                finally:
                    if hasattr(site, 'browser') and site.browser and site.browser.is_running():
                        print("\nShutting down site handler...")
                        site.stop_browser()
                        print("Site handler closed.")
            
        return 0
    
    else:
        print("Please specify a command. Use --help for more information.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
