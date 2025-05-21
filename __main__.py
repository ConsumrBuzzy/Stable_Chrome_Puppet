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
        from core import ChromePuppet
        browser = ChromePuppet(headless=args.headless)
        try:
            print("Browser launched successfully!")
            print("Press Ctrl+C to exit...")
            while True:
                pass
        except KeyboardInterrupt:
            print("\nShutting down browser...")
            browser.quit()
        return 0
    
    else:
        print("Please specify a command. Use --help for more information.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
