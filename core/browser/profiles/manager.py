"""
Profile management for browser automation.

This module provides functionality to manage browser profiles,
including listing, validating, and selecting profiles.
"""
import logging
import os
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .profile import Profile

logger = logging.getLogger(__name__)


class ProfileManager:
    """Manages browser profiles and their configurations.
    
    This class provides methods to discover, validate, and manage
    browser profiles for different operating systems.
    """
    
    # Profiles to ignore when discovering
    IGNORED_PROFILES = ["System Profile", "Guest Profile"]
    
    # Default profile names for different browsers
    DEFAULT_PROFILE_NAMES = {
        'chrome': 'Default',
        'chrome-beta': 'Default',
        'chrome-dev': 'Default',
        'chrome-canary': 'Default',
        'chromium': 'Default',
        'edge': 'Default',
        'brave': 'Default',
        'opera': 'Default',
        'vivaldi': 'Default',
    }
    
    def __init__(self, user_data_dir: Optional[Union[str, Path]] = None, 
                 browser: str = 'chrome'):
        """Initialize the ProfileManager.
        
        Args:
            user_data_dir: Optional path to the browser's user data directory.
                          If not provided, uses the default for the specified browser.
            browser: Name of the browser (e.g., 'chrome', 'edge'). Defaults to 'chrome'.
        """
        self.browser = browser.lower()
        self.user_data_dir = Path(user_data_dir) if user_data_dir else self.get_default_user_data_dir()
        self.profiles: Dict[str, Profile] = {}
        self._discover_profiles()
    
    @classmethod
    def get_default_user_data_dir(cls, browser: Optional[str] = None) -> Path:
        """Get the default user data directory for the specified browser.
        
        Args:
            browser: Name of the browser. If None, uses the instance's browser.
            
        Returns:
            Path to the default user data directory.
            
        Raises:
            ValueError: If the browser is not supported.
        """
        browser = (browser or 'chrome').lower()
        
        # Map of browser names to their default paths
        browser_paths = {
            'chrome': cls._get_chrome_user_data_dir(),
            'chrome-beta': cls._get_chrome_user_data_dir('Chrome Beta'),
            'chrome-dev': cls._get_chrome_user_data_dir('Chrome Dev'),
            'chrome-canary': cls._get_chrome_user_data_dir('Chrome SxS'),
            'chromium': cls._get_chrome_user_data_dir('Chromium'),
            'edge': cls._get_edge_user_data_dir(),
            'brave': cls._get_brave_user_data_dir(),
            'opera': cls._get_opera_user_data_dir(),
            'vivaldi': cls._get_vivaldi_user_data_dir(),
        }
        
        if browser not in browser_paths:
            raise ValueError(f"Unsupported browser: {browser}")
            
        return browser_paths[browser]
    
    @staticmethod
    def _get_chrome_user_data_dir(browser_name: str = 'Google/Chrome') -> Path:
        """Get the Chrome user data directory for the current platform."""
        if os.name == 'nt':  # Windows
            return Path(os.path.expandvars(r'%LOCALAPPDATA%')) / browser_name / 'User Data'
        elif os.name == 'posix':  # macOS/Linux
            if platform.system() == 'Darwin':  # macOS
                return Path(f'~/Library/Application Support/{browser_name}').expanduser()
            return Path(f'~/.config/{browser_name.lower()}').expanduser()
        return Path('')
    
    @staticmethod
    def _get_edge_user_data_dir() -> Path:
        """Get the Microsoft Edge user data directory for the current platform."""
        if os.name == 'nt':
            return Path(os.path.expandvars(r'%LOCALAPPDATA%')) / 'Microsoft' / 'Edge' / 'User Data'
        elif os.name == 'posix':
            if platform.system() == 'Darwin':
                return Path('~/Library/Application Support/Microsoft Edge').expanduser()
            return Path('~/.config/microsoft-edge').expanduser()
        return Path('')
    
    @staticmethod
    def _get_brave_user_data_dir() -> Path:
        """Get the Brave browser user data directory for the current platform."""
        if os.name == 'nt':
            return Path(os.path.expandvars(r'%LOCALAPPDATA%')) / 'BraveSoftware' / 'Brave-Browser' / 'User Data'
        elif os.name == 'posix':
            if platform.system() == 'Darwin':
                return Path('~/Library/Application Support/BraveSoftware/Brave-Browser').expanduser()
            return Path('~/.config/BraveSoftware/Brave-Browser').expanduser()
        return Path('')
    
    @staticmethod
    def _get_opera_user_data_dir() -> Path:
        """Get the Opera browser user data directory for the current platform."""
        if os.name == 'nt':
            return Path(os.path.expandvars(r'%APPDATA%')) / 'Opera Software' / 'Opera Stable'
        elif os.name == 'posix':
            if platform.system() == 'Darwin':
                return Path('~/Library/Application Support/com.operasoftware.Opera').expanduser()
            return Path('~/.config/opera').expanduser()
        return Path('')
    
    @staticmethod
    def _get_vivaldi_user_data_dir() -> Path:
        """Get the Vivaldi browser user data directory for the current platform."""
        if os.name == 'nt':
            return Path(os.path.expandvars(r'%LOCALAPPDATA%')) / 'Vivaldi' / 'User Data'
        elif os.name == 'posix':
            if platform.system() == 'Darwin':
                return Path('~/Library/Application Support/Vivaldi').expanduser()
            return Path('~/.config/vivaldi').expanduser()
        return Path('')
    
    def _discover_profiles(self) -> None:
        """Discover all available profiles in the user data directory."""
        self.profiles.clear()
        
        if not self.user_data_dir.exists():
            logger.warning(f"Browser user data directory not found: {self.user_data_dir}")
            return
        
        # Check for profile directories
        profile_dirs = []
        
        # Look for profile directories (e.g., 'Default', 'Profile 1')
        for item in self.user_data_dir.iterdir():
            if item.is_dir() and item.name not in self.IGNORED_PROFILES:
                if item.name.startswith('Profile ') or item.name == 'Default':
                    profile_dirs.append(item)
        
        # If no profile directories found, use the user data directory itself
        if not profile_dirs and self.user_data_dir.exists():
            profile_dirs = [self.user_data_dir]
        
        # Create Profile objects for each directory
        for profile_dir in profile_dirs:
            profile_name = profile_dir.name
            is_default = profile_name == 'Default' or profile_name == self.DEFAULT_PROFILE_NAMES.get(self.browser, 'Default')
            
            profile = Profile(
                name=profile_name,
                path=profile_dir,
                is_default=is_default
            )
            
            self.profiles[profile_name] = profile
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """List all available profiles with their details.
        
        Returns:
            List of dictionaries containing profile information.
        """
        return [profile.to_dict() for profile in self.profiles.values()]
    
    def get_profile(self, name: str) -> Optional[Profile]:
        """Get a profile by name.
        
        Args:
            name: Name of the profile to retrieve.
            
        Returns:
            Profile instance if found, None otherwise.
        """
        return self.profiles.get(name)
    
    def get_default_profile(self) -> Optional[Profile]:
        """Get the default profile.
        
        Returns:
            Default Profile instance if found, None otherwise.
        """
        for profile in self.profiles.values():
            if profile.is_default:
                return profile
        return None
    
    def validate_profile(self, name: str) -> Tuple[bool, str]:
        """Validate if a profile exists and is accessible.
        
        Args:
            name: Name of the profile to validate.
            
        Returns:
            Tuple of (is_valid, message).
        """
        if not name:
            return False, "Profile name cannot be empty"
            
        profile = self.get_profile(name)
        if not profile:
            return False, f"Profile '{name}' not found"
            
        return profile.validate()
    
    @classmethod
    def select_profile_interactive(cls, profiles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Interactively select a profile from the list.
        
        Args:
            profiles: List of profile dictionaries from list_profiles()
            
        Returns:
            Selected profile dictionary, or None if no selection made
        """
        if not profiles:
            print("\nNo profiles found.")
            return None
        
        print("\nAvailable browser profiles:")
        print("-" * 60)
        
        # Sort profiles: Default first, then alphabetically
        sorted_profiles = sorted(
            profiles,
            key=lambda x: (not x['is_default'], x['name'].lower())
        )
        
        # Display profiles with details
        for i, profile in enumerate(sorted_profiles, 1):
            default_marker = " (Default)" if profile['is_default'] else ""
            valid_status = "✓" if profile.get('is_valid', True) else "✗"
            print(f"  {i:2d}. {valid_status} {profile['name']}{default_marker}")
            print(f"      Path: {profile['path']}")
            print(f"      Size: {profile['size_mb']:.2f} MB\n")
        
        print("  Enter profile number or press Enter to cancel")
        print("  " + "-" * 50)
        
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
