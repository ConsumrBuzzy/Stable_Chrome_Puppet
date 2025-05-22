"""
Simple script to load Google with a specific Chrome profile.

This script will list all available Chrome profiles and let you select one.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

# Add parent directory to path to allow importing from core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.browser.drivers.chrome import ChromeBrowser
from core.config import ChromeConfig

def get_default_chrome_user_data_dir() -> str:
    """Get the default Chrome user data directory based on OS."""
    if sys.platform.startswith('win'):
        return os.path.expandvars(r'%LOCALAPPDATA%\\Google\\Chrome\\User Data')
    elif sys.platform.startswith('darwin'):
        return os.path.expanduser('~/Library/Application Support/Google/Chrome')
    else:  # Linux and others
        return os.path.expanduser('~/.config/google-chrome')

def list_chrome_profiles(user_data_dir: str) -> list[str]:
    """List all available Chrome profiles in the user data directory.
    
    Args:
        user_data_dir: Path to the Chrome user data directory.
        
    Returns:
        List of profile names.
    """
    profiles = []
    profiles_path = Path(user_data_dir)
    
    if not profiles_path.exists():
        print(f"\nWarning: Chrome user data directory not found: {user_data_dir}")
        return []
    
    # Look for profile directories
    for item in profiles_path.iterdir():
        if item.is_dir() and item.name not in ["System Profile", "Guest Profile"]:
            profiles.append(item.name)
    
    # Print all available profiles
    if profiles:
        print("\nAvailable Chrome profiles:")
        for i, profile in enumerate(sorted(profiles), 1):
            print(f"  {i}. {profile}")
    else:
        print("\nNo Chrome profiles found in:")
        print(f"  {user_data_dir}")
    
    return profiles

def select_profile_interactively(profiles: list[str]) -> str:
    """Let the user select a profile from the list.
    
    Args:
        profiles: List of available profile names.
        
    Returns:
        Selected profile name or "Default" if no selection made.
    """
    if not profiles:
        print("\nNo profiles available. Using 'Default' profile.")
        return "Default"
    
    # Sort profiles for consistent ordering
    sorted_profiles = sorted(profiles)
    
    print("\nAvailable Chrome profiles:")
    for i, profile in enumerate(sorted_profiles, 1):
        print(f"  {i}. {profile}")
    
    print("\n  Enter profile number or press Enter for Default")
    print("  --------------------------------------------")
    
    while True:
        try:
            choice = input("\n  Your choice: ").strip()
            if not choice:
                print("\nUsing 'Default' profile.")
                return "Default"
            
            index = int(choice) - 1
            if 0 <= index < len(sorted_profiles):
                selected = sorted_profiles[index]
                print(f"\nSelected profile: {selected}")
                return selected
                
            print(f"  Please enter a number between 1 and {len(sorted_profiles)}")
        except ValueError:
            print("  Please enter a valid number or press Enter for Default")

def main():
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Load Google with a Chrome profile')
    parser.add_argument('--profile', type=str, default=None,
                      help='Chrome profile name (e.g., "Profile 1", "Default")')
    parser.add_argument('--user-data-dir', type=str, default=None,
                      help=f'Custom Chrome user data directory (default: {get_default_chrome_user_data_dir()})')
    parser.add_argument('--list-profiles', action='store_true',
                      help='List available profiles and exit')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Get user data directory
    user_data_dir = args.user_data_dir or get_default_chrome_user_data_dir()
    
    # List profiles if requested
    if args.list_profiles:
        profiles = list_chrome_profiles(user_data_dir)
        print("\nAvailable Chrome profiles:")
        for profile in profiles or ['Default']:
            print(f"- {profile}")
        return
    
    # Get profile to use
    profile = args.profile
    if profile is None:
        profiles = list_chrome_profiles(user_data_dir)
        profile = select_profile_interactively(profiles)
    
    logger.info(f"Using Chrome profile: {profile}")
    
    # Verify profile directory exists
    profile_path = Path(user_data_dir) / profile
    if not profile_path.exists():
        logger.warning(f"Profile directory does not exist: {profile_path}")
        logger.info("Available profiles in user data directory:")
        for p in Path(user_data_dir).glob("*"):
            if p.is_dir() and p.name not in ["System Profile", "Guest Profile"]:
                logger.info(f"- {p.name}")
    else:
        logger.debug(f"Using profile directory: {profile_path}")
    
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
            f'--profile-directory={profile}',
            f'--user-data-dir={user_data_dir}'
        ]
    )
    
    # Initialize and start browser
    browser = ChromeBrowser(config=config)
    
    try:
        logger.info(f"Starting browser with profile: {profile}")
        logger.debug(f"User data directory: {user_data_dir}")
        logger.debug(f"Profile directory: {profile}")
        
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

if __name__ == "__main__":
    main()
