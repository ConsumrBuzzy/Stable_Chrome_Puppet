"""
Test script for ProfileManager to list Chrome profiles with detailed information.
"""
import logging
import sys
from pathlib import Path

# Add parent directory to path to allow importing from core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.browser.profile_manager import ProfileManager

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('profile_manager_test.log', mode='w')
        ]
    )

def print_profile_details(profile):
    """Print detailed information about a profile."""
    print("\n" + "="*80)
    print(f"PROFILE: {profile.get('display_name', profile['name'])}")
    print("="*80)
    
    # Basic info
    print(f"Name:      {profile.get('name')}")
    print(f"Type:      {profile.get('profile_type', 'unknown')}")
    print(f"Path:      {profile.get('path')}")
    print(f"Size:      {profile.get('size_mb', 0):.2f} MB")
    
    # Email information
    emails = []
    if 'email' in profile and profile['email']:
        emails.append(profile['email'])
    if 'emails' in profile and profile['emails']:
        emails.extend([e for e in profile['emails'] if e and e not in emails])
    
    if emails:
        print("\nEmails:")
        for i, email in enumerate(emails, 1):
            prefix = "* " if i == 1 and len(emails) > 1 else "  "
            print(f"{prefix}{email}")
    
    # Account information
    if 'account_info' in profile and profile['account_info']:
        print("\nAccounts:")
        for account_id, account in profile['account_info'].items():
            print(f"- ID: {account_id}")
            for key, value in account.items():
                if value:  # Only show non-empty fields
                    print(f"  {key}: {value}")

def main():
    """Main function to test the ProfileManager."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Try with auto-detection first
        logger.info("Initializing ProfileManager with auto-detection...")
        pm = ProfileManager()
        
        # List all profiles with details
        profiles = pm.list_profiles(include_details=True)
        
        if not profiles:
            print("\nNo Chrome profiles found!")
            return
        
        print(f"\nFound {len(profiles)} Chrome profiles:")
        for profile in profiles:
            print_profile_details(profile)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\nError: {e}")
        
        # Try with the user's specific directory
        user_dir = r"C:\Users\cheat\AppData\Local\Google\Chrome\User Data"
        logger.info(f"Trying with specific user directory: {user_dir}")
        try:
            pm = ProfileManager(user_dir)
            profiles = pm.list_profiles(include_details=True)
            
            if not profiles:
                print("\nNo Chrome profiles found in the specified directory!")
                return
            
            print(f"\nFound {len(profiles)} Chrome profiles in {user_dir}:")
            for profile in profiles:
                print_profile_details(profile)
                
        except Exception as e2:
            logger.error(f"Error with specific directory: {e2}", exc_info=True)
            print(f"\nError with specific directory: {e2}")

if __name__ == "__main__":
    main()
