"""
Simple script to load Google with a specific Chrome profile.

This script demonstrates how to use the Chrome browser automation with profile management.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path to allow importing from core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.browser.drivers.chrome import ChromeBrowser
from core.browser.profile_manager import ProfileManager, select_profile_interactive
from core.config import ChromeConfig

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
            logging.StreamHandler()
        ]
    )
    
    # Reduce logging from Selenium and other libraries
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

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
        
        # List profiles and exit if requested
        if args.list_profiles:
            print("\n" + "="*50)
            print("Available Chrome Profiles")
            print("="*50)
            
            # List profiles by type
            for profile_type, title in [
                ('user', 'User Profiles'),
                ('development', 'Development Profiles'),
                ('system', 'System Profiles')
            ]:
                profiles = profile_manager.list_profiles(profile_type)
                if profiles:
                    print(f"\n{title}:")
                    print("-" * 50)
                    for i, profile in enumerate(profiles, 1):
                        display_name = profile.get('display_name', profile['name'])
                        email = f" ({profile['email']})" if profile.get('email') else ""
                        size = f"{profile.get('size_mb', 0):.2f} MB"
                        print(f"{i:3d}. {display_name}{email}")
                        print(f"     Path: {profile['path']}")
                        print(f"     Size: {size}")
            
            total = len(profile_manager.profiles)
            print(f"\nTotal profiles found: {total}")
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
            chrome_arguments=[
                '--disable-notifications',
                '--start-maximized',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-dev-shm-usage',
                '--no-sandbox',
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
