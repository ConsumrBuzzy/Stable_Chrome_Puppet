"""Run all Chrome Puppet tests."""
import unittest
import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path to import our package
sys.path.insert(0, str(Path(__file__).parent.absolute()))

def run_tests(headless=True, test_name=None):
    """Run all tests or a specific test.
    
    Args:
        headless: Whether to run browser in headless mode
        test_name: Name of specific test to run (e.g., 'test_browser_init')
    """
    # Set headless mode in environment for tests
    os.environ['HEADLESS_MODE'] = str(headless).lower()
    
    # Discover and run tests
    test_dir = os.path.join(os.path.dirname(__file__), 'tests')
    if test_name:
        # Run specific test
        test_suite = unittest.defaultTestLoader.discover(
            test_dir, 
            pattern=f'test_{test_name}.py'
        )
    else:
        # Run all tests
        test_suite = unittest.defaultTestLoader.discover(test_dir)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return appropriate exit code
    sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Chrome Puppet tests')
    parser.add_argument(
        '--no-headless', 
        action='store_true', 
        help='Run tests with visible browser window'
    )
    parser.add_argument(
        '--test',
        type=str,
        help='Run a specific test (e.g., "browser_init" for test_browser_init.py)'
    )
    
    args = parser.parse_args()
    run_tests(headless=not args.no_headless, test_name=args.test)
