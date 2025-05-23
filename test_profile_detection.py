#!/usr/bin/env python3
"""
Simple script to test Chrome profile detection.
"""
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Test Chrome profile detection."""
    try:
        from core.browser.profile_manager import ProfileManager
        
        logger.info("Initializing ProfileManager...")
        manager = ProfileManager()
        
        logger.info("Listing all profiles...")
        profiles = manager.list_profiles(include_details=True)
        
        if not profiles:
            logger.warning("No Chrome profiles found!")
            return
            
        logger.info("Found %d profiles", len(profiles))
        
        # Print summary of all profiles
        print("\n" + "="*80)
        print(f"Found {len(profiles)} Chrome profiles:")
        print("="*80)
        
        for i, (name, info) in enumerate(profiles.items(), 1):
            print(f"\nProfile {i}: {name}")
            print("-" * 50)
            print(f"Display Name: {info.get('display_name', 'N/A')}")
            print(f"Email: {info.get('email', 'No email found')}")
            print(f"Type: {info.get('profile_type', 'unknown')}")
            print(f"Path: {info.get('path')}")
            print(f"Size: {info.get('size_mb', 0):.2f} MB")
            print(f"Last Modified: {info.get('last_modified', 'Unknown')}")
            
            # Show account info if available
            if info.get('account_info'):
                print("\nAccount Info:")
                for acc_id, acc in info['account_info'].items():
                    print(f"  - {acc.get('email')} ({acc.get('name')})")
            
            # Show statistics
            stats = [
                ("History Items", info.get('history_count', 0)),
                ("Bookmarks", info.get('bookmark_count', 0)),
                ("Saved Logins", info.get('login_data_count', 0)),
                ("Autofill Profiles", info.get('autofill_count', 0)),
                ("Saved Credit Cards", info.get('credit_card_count', 0))
            ]
            
            print("\nStatistics:")
            for label, count in stats:
                print(f"  - {label}: {count:,}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        logger.exception("Error testing profile detection:")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
