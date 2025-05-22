"""
Simple script to load Google with a specific Chrome profile.

This script demonstrates how to use the Chrome browser automation with profile management.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add parent directory to path to allow importing from core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.browser.drivers.chrome import ChromeBrowser
from core.browser.profile_manager import ProfileManager, select_profile_interactive, format_size
from core.config import ChromeConfig

def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.
    
    Args:
        verbose: If True, set log level to DEBUG
    """
    # Always use DEBUG level for our logger
    log_level = logging.DEBUG
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler with a higher log level
    console = logging.StreamHandler()
    console.setLevel(log_level if verbose else logging.INFO)
    console.setFormatter(formatter)
    
    # Create file handler which logs debug messages
    file_handler = logging.FileHandler('chrome_puppet.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Get the root logger and add handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add the handlers
    root_logger.addHandler(console)
    root_logger.addHandler(file_handler)
    
    # Set specific log levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('webdriver_manager').setLevel(logging.WARNING)
    
    # Enable our own debug logging
    logging.getLogger('core.browser').setLevel(logging.DEBUG)
    logging.getLogger('core.browser.profile_manager').setLevel(logging.DEBUG)
    
    logger = logging.getLogger(__name__)
    logger.debug("Logging initialized with debug level")

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Load Google in Chrome with a specific profile')
    parser.add_argument('--profile', type=str, help='Chrome profile to use')
    parser.add_argument('--user-data-dir', type=str, help='Custom Chrome user data directory')
    parser.add_argument('--list-profiles', action='store_true', 
                       help='List available profiles and exit')
    parser.add_argument('--profile-type', type=str, choices=['user', 'development', 'system'],
                       help='Filter profiles by type (user, development, system)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize profile manager
        logger.debug(f"Using Chrome user data directory: {args.user_data_dir or 'default'}")
        profile_manager = ProfileManager(user_data_dir=args.user_data_dir)
        
        # List profiles only if requested
        if args.list_profiles:
            print("\n" + "="*80)
            print("CHROME PROFILES".center(80))
            print("="*80)
            
            try:
                # Get all profiles
                all_profiles = profile_manager.list_profiles()
                
                if not all_profiles:
                    print("\nNo Chrome profiles found!")
                    return
                    
                # Print basic profile list
                print("\nAvailable Profiles:")
                print("-" * 80)
                
                for i, profile in enumerate(all_profiles, 1):
                    name = str(profile.get('display_name', profile.get('name', 'Unnamed')))
                    email = str(profile.get('email', ''))
                    ptype = profile.get('profile_type', 'user').title()
                    size = format_size(profile.get('size_mb', 0))
                    
                    print(f"{i:2d}. {name:<30} {email:<30} {ptype:<12} {size}")
                
                # Print summary
                print("\n" + "="*80)
                print(f"Found {len(all_profiles)} profiles")
                
            except Exception as e:
                print(f"\nError listing profiles: {e}")
                logger.exception("Error in profile listing:")
            
            return
        
        # Get profile to use
        selected_profile = None
        if args.profile:
            # Use specified profile
            profiles = [p for p in profile_manager.list_profiles() 
                      if p['name'] == args.profile or p.get('display_name') == args.profile]
            
            if profiles:
                selected_profile = profiles[0]
                logger.info(f"Using specified profile: {selected_profile.get('display_name', selected_profile['name'])}")
            else:
                logger.warning(f"Profile '{args.profile}' not found.")
        
        # If no valid profile specified, prompt user to select one
        if not selected_profile:
            profiles = profile_manager.list_profiles(args.profile_type)
            if not profiles:
                logger.error("No profiles found matching the specified criteria.")
                return
                
            selected_profile = select_profile_interactive(profiles)
            if not selected_profile:
                logger.info("No profile selected. Exiting.")
                return
        
        logger.info(f"Using Chrome profile: {selected_profile.get('display_name', selected_profile['name'])}")
        
        # Configure Chrome with profile settings
        config = ChromeConfig(
            headless=False,  # Show browser window
            window_size=(1920, 1080),  # Set explicit window size
            chrome_arguments=[
                '--disable-notifications',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-dev-shm-usage',
                '--disable-browser-side-navigation',
                '--no-sandbox',
                '--disable-features=VizDisplayCompositor',
                '--disable-background-networking',
                '--disable-client-side-phishing-detection',
                '--disable-component-update',
                '--disable-hang-monitor',
                '--disable-popup-blocking',
                '--disable-prompt-on-repost',
                '--disable-sync',
                '--disable-translate',
                '--metrics-recording-only',
                '--safebrowsing-disable-auto-update',
                '--disable-web-security',  # Only for testing, remove in production
                '--allow-running-insecure-content',  # Only for testing, remove in production
                f'--profile-directory={selected_profile["name"]}',
                f'--user-data-dir={os.path.dirname(selected_profile["path"])}'
            ]
        )
        
        # Initialize and start browser
        browser = ChromeBrowser(config=config)
        
        try:
            logger.info(f"Starting browser with profile: {selected_profile['name']}")
            logger.debug(f"Profile path: {selected_profile['path']}")
            
            # Start the browser
            browser.start()
            logger.info("Browser started successfully")
            
            # Navigate to Google
            logger.info("Navigating to Google...")
            browser.driver.get('https://www.google.com')
            logger.info("Page loaded successfully. Press Ctrl+C to exit.")
            
            # Keep browser open until interrupted
            while True:
                try:
                    import time
                    time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("\nShutdown requested by user")
                    break
                
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
        finally:
            try:
                logger.info("Stopping browser...")
                browser.stop()
                logger.info("Browser stopped successfully")
            except Exception as e:
                logger.error(f"Error while stopping browser: {e}", exc_info=True)
                
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    main()
