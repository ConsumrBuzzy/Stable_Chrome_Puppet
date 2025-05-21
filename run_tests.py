"""Run all Chrome Puppet tests."""
import os
import sys
import argparse
import unittest
from pathlib import Path
from typing import Optional, List

# Add parent directory to path to import our package
sys.path.insert(0, str(Path(__file__).parent.absolute()))

def run_tests(
    headless: bool = True,
    test_name: Optional[str] = None,
    test_dir: str = 'tests',
    pattern: str = 'test_*.py',
    verbosity: int = 2
) -> bool:
    """Run tests with the specified configuration.
    
    Args:
        headless: Whether to run browser in headless mode
        test_name: Name of specific test to run (e.g., 'browser_init')
        test_dir: Directory containing test files
        pattern: Pattern to match test files
        verbosity: Verbosity level (0=quiet, 1=normal, 2=verbose)
        
    Returns:
        bool: True if all tests passed, False otherwise
    """
    # Set headless mode in environment for tests
    os.environ['HEADLESS_MODE'] = str(headless).lower()
    
    # Set up test discovery
    test_dir_path = Path(test_dir)
    if not test_dir_path.exists():
        print(f"Error: Test directory '{test_dir}' not found")
        return False
    
    # If a specific test is specified, adjust the pattern
    if test_name:
        if not test_name.startswith('test_'):
            test_name = f'test_{test_name}'
        if not test_name.endswith('.py'):
            test_name = f'{test_name}.py'
        pattern = test_name
    
    try:
        # Discover and run tests
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover(
            start_dir=str(test_dir_path),
            pattern=pattern
        )
        
        if test_suite.countTestCases() == 0:
            print(f"No tests found matching pattern '{pattern}' in {test_dir}")
            return False
            
        # Run the tests
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(test_suite)
        
        # Print summary
        print("\n" + "=" * 70)
        if result.wasSuccessful():
            print(f"All {result.testsRun} tests passed!")
        else:
            print(f"Tests failed: {len(result.failures) + len(result.errors)}/{result.testsRun}")
            
            if result.failures:
                print("\nFailures:")
                for failure in result.failures:
                    print(f"\n{failure[0]}")
                    print(failure[1])
                    
            if result.errors:
                print("\nErrors:")
                for error in result.errors:
                    print(f"\n{error[0]}")
                    print(error[1])
        
        print("=" * 70)
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        return False

def main():
    """Parse command line arguments and run tests."""
    parser = argparse.ArgumentParser(
        description='Run Chrome Puppet tests',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
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
    parser.add_argument(
        '--test-dir',
        type=str,
        default='tests',
        help='Directory containing test files'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='test_*.py',
        help='Pattern to match test files'
    )
    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        choices=[0, 1, 2],
        default=2,
        help='Set the verbosity level (0=quiet, 1=normal, 2=verbose)'
    )
    
    args = parser.parse_args()
    
    success = run_tests(
        headless=not args.no_headless,
        test_name=args.test,
        test_dir=args.test_dir,
        pattern=args.pattern,
        verbosity=args.verbosity
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
