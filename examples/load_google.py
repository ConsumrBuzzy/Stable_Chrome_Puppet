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
        
        # List profiles only if requested
        if args.list_profiles:
            print("\n" + "="*80)
            print("CHROME PROFILE MANAGER")
            print("="*80)
            
            # Get profiles based on filter if provided
            if args.profile_type:
                profiles = profile_manager.list_profiles(profile_type=args.profile_type)
                if not profiles:
                    print(f"\nNo {args.profile_type} profiles found.")
                    return
            else:
                profiles = profile_manager.list_profiles()
            
            # Sort profiles by type and name
            def get_profile_sort_key(p):
                profile_type = p.get('profile_type', 'user')
                type_order = {'user': 0, 'development': 1, 'system': 2}.get(profile_type, 3)
                return (type_order, p.get('display_name', '').lower())
            
            profiles.sort(key=get_profile_sort_key)
            
            # Print summary header
            print(f"\n{'#':>3}  {'Profile Name':<30} {'Email':<30} {'Size':>10}")
            print("-" * 80)
            
            # Print each profile in the list
            for i, profile in enumerate(profiles, 1):
                display_name = profile.get('display_name', profile['name'])
                if len(display_name) > 28:
                    display_name = display_name[:25] + '...'
                    
                email = profile.get('email', '')
                if email and len(email) > 28:
                    email = email[:25] + '...'
                    
                size = format_size(profile.get('size_mb', 0))
                print(f"{i:3d}. {display_name:<30} {email:<30} {size:>10}")
            
            # Print detailed information for each profile
            print("\n" + "="*80)
            print("DETAILED PROFILE INFORMATION")
            print("="*80)
            
            for i, profile in enumerate(profiles, 1):
                print(f"\n[{i}] {profile.get('display_name', profile['name'])}")
                print("-" * 80)
                
                # Basic info
                print(f"Name:    {profile.get('display_name', profile['name'])}")
                if 'email' in profile and profile['email']:
                    print(f"Email:   {profile['email']}")
                print(f"Type:    {profile.get('profile_type', 'user').title()}")
                print(f"Path:    {profile['path']}")
                print(f"Size:    {format_size(profile.get('size_mb', 0))}")
                
                # Last modified time if available
                if 'last_modified' in profile and profile['last_modified']:
                    from datetime import datetime
                    mod_time = datetime.fromtimestamp(profile['last_modified'])
                    print(f"Updated: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            print(f"\nTotal profiles found: {len(profiles)}")
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
