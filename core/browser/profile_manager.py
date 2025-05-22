"""
Profile management for browser automation.

This module provides functionality to manage browser profiles,
including listing, validating, and selecting profiles.
"""
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class ProfileManager:
    """Manages browser profiles and their configurations."""
    
    IGNORED_PROFILES = ["System Profile", "Guest Profile"]
    
    def __init__(self, user_data_dir: Optional[str] = None):
        """Initialize the ProfileManager.
        
        Args:
            user_data_dir: Optional path to the Chrome user data directory.
                          If not provided, uses the default Chrome user data directory.
        """
        self.user_data_dir = user_data_dir or self.get_default_user_data_dir()
        self.profiles: Dict[str, Path] = {}
        self._discover_profiles()
    
    @staticmethod
    def get_default_user_data_dir() -> str:
        """Get the default Chrome user data directory based on the OS."""
        if os.name == 'nt':  # Windows
            return os.path.expandvars(r'%LOCALAPPDATA%\\Google\\Chrome\\User Data')
        elif os.name == 'posix':  # macOS/Linux
            if os.uname().sysname == 'Darwin':  # macOS
                return os.path.expanduser('~/Library/Application Support/Google/Chrome')
            return os.path.expanduser('~/.config/google-chrome')
        return ''
    
    def _discover_profiles(self) -> None:
        """Discover all available profiles in the user data directory."""
        self.profiles.clear()
        profiles_path = Path(self.user_data_dir)
        
        if not profiles_path.exists():
            logger.warning(f"Chrome user data directory not found: {profiles_path}")
            return
        
        # Find all profile directories
        for item in profiles_path.iterdir():
            if item.is_dir() and item.name not in self.IGNORED_PROFILES:
                self.profiles[item.name] = item
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """List all available profiles with their details.
        
        Returns:
            List of dictionaries containing profile information.
        """
        profiles = []
        for name, path in sorted(self.profiles.items()):
            profiles.append({
                'name': name,
                'path': str(path),
                'is_default': name.lower() == 'default',
                'size_mb': self._get_directory_size_mb(path)
            })
        return profiles
    
    def get_profile_path(self, profile_name: str) -> Optional[Path]:
        """Get the path to a specific profile.
        
        Args:
            profile_name: Name of the profile.
            
        Returns:
            Path to the profile directory, or None if not found.
        """
        return self.profiles.get(profile_name)
    
    def validate_profile(self, profile_name: str) -> Tuple[bool, str]:
        """Validate if a profile exists and is accessible.
        
        Args:
            profile_name: Name of the profile to validate.
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not profile_name:
            return False, "Profile name cannot be empty"
            
        profile_path = self.get_profile_path(profile_name)
        if not profile_path:
            return False, f"Profile '{profile_name}' not found"
            
        if not profile_path.exists():
            return False, f"Profile directory does not exist: {profile_path}"
            
        return True, f"Profile '{profile_name}' is valid"
    
    @staticmethod
    def _get_directory_size_mb(directory: Path) -> float:
        """Calculate the size of a directory in MB."""
        try:
            total_size = sum(f.stat().st_size for f in directory.glob('**/*') if f.is_file())
            return round(total_size / (1024 * 1024), 2)  # Convert to MB
        except Exception as e:
            logger.warning(f"Could not calculate size for {directory}: {e}")
            return 0.0


def select_profile_interactive(profiles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Interactively select a profile from the list.
    
    Args:
        profiles: List of profile dictionaries from ProfileManager.list_profiles()
        
    Returns:
        Selected profile dictionary, or None if no selection made
    """
    if not profiles:
        print("\nNo profiles found.")
        return None
    
    print("\nAvailable Chrome profiles:")
    print("-" * 40)
    
    # Sort profiles: Default first, then alphabetically
    sorted_profiles = sorted(
        profiles,
        key=lambda x: (not x['is_default'], x['name'].lower())
    )
    
    # Display profiles with details
    for i, profile in enumerate(sorted_profiles, 1):
        default_marker = " (Default)" if profile['is_default'] else ""
        print(f"  {i:2d}. {profile['name']}{default_marker}")
        print(f"      Path: {profile['path']}")
        print(f"      Size: {profile['size_mb']:.2f} MB\n")
    
    print("  Enter profile number or press Enter to cancel")
    print("  " + "-" * 36)
    
    while True:
        try:
            choice = input("\n  Your choice: ").strip()
            if not choice:
                print("\nNo profile selected.")
                return None
            
            index = int(choice) - 1
            if 0 <= index < len(sorted_profiles):
                selected = sorted_profiles[index]
                print(f"\nSelected profile: {selected['name']}")
                return selected
                
            print(f"  Please enter a number between 1 and {len(sorted_profiles)}")
        except ValueError:
            print("  Please enter a valid number or press Enter to cancel")
