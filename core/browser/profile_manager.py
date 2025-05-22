"""
Profile management for browser automation.

This module provides functionality to manage browser profiles,
including listing, validating, and selecting profiles.
"""
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, TypedDict

logger = logging.getLogger(__name__)

class ProfileInfo(TypedDict):
    """Type definition for profile information."""
    name: str
    path: str
    profile_type: str
    size_mb: float
    email: Optional[str]
    display_name: Optional[str]

class ProfileManager:
    """Manages browser profiles and their configurations."""
    
    # System profiles that should be ignored
    IGNORED_PROFILES = ["System Profile", "Guest Profile"]
    
    # Known system/development profile names
    SYSTEM_PROFILES = [
        # System profiles
        "System Profile", "Guest Profile", "Crashpad", "Metrics Reporting", 
        "ShaderCache", "GrShaderCache", "WidevineCdm", "MEIPreload",
        # Development/extension related
        "Extension State", "Extensions", "Extension Rules", "Extension Scripts",
        # Cache and temporary data
        "Cache", "Code Cache", "GPUCache", "Service Worker", "DawnCache",
        # Security and certificates
        "Safe Browsing", "SSLErrorAssistant", "CertificateRevocation", "PKIMetadata",
        # Other system components
        "BrowserMetrics", "FileTypePolicies", "OriginTrials", "OptimizationHints",
        "Subresource Filter", "Webstore Downloads", "ZxcvbnData"
    ]
    
    def __init__(self, user_data_dir: Optional[str] = None):
        """Initialize the ProfileManager.
        
        Args:
            user_data_dir: Optional path to the Chrome user data directory.
                          If not provided, uses the default Chrome user data directory.
        """
        self.user_data_dir = user_data_dir or self.get_default_user_data_dir()
        self.profiles: Dict[str, Dict[str, Any]] = {}
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
    
    def _get_profile_type(self, profile_name: str) -> str:
        """Determine the type of profile based on its name.
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            str: Profile type ('system', 'development', or 'user')
        """
        if any(profile_name.startswith(p) or profile_name == p for p in self.SYSTEM_PROFILES):
            return 'system'
        elif any(x in profile_name.lower() for x in ['dev', 'test', 'staging', 'local']):
            return 'development'
        return 'user'
    
    def _get_profile_info(self, profile_path: Path) -> Dict[str, Any]:
        """Get additional information about a profile.
        
        Args:
            profile_path: Path to the profile directory
            
        Returns:
            Dict containing profile information with the following keys:
            - name: The directory name of the profile
            - path: Full path to the profile directory
            - size_mb: Size of the profile in MB
            - email: Email associated with the profile (if any)
            - display_name: User-friendly name for the profile
            - last_modified: Timestamp of when the profile was last modified
        """
        try:
            # Get basic file info
            stat_info = profile_path.stat()
            
            info = {
                'name': profile_path.name,
                'path': str(profile_path),
                'size_mb': self._get_directory_size(profile_path) / (1024 * 1024),
                'email': None,
                'display_name': None,
                'last_modified': stat_info.st_mtime
            }
            
            # Try to get profile name and email from preferences file
            prefs_file = profile_path / 'Preferences'
            if prefs_file.exists():
                try:
                    with open(prefs_file, 'r', encoding='utf-8') as f:
                        prefs = json.load(f)
                        
                    # Get email from sync account info
                    if 'profile' in prefs and 'info_cache' in prefs['profile']:
                        for cache in prefs['profile']['info_cache'].values():
                            if 'email' in cache and cache['email']:
                                info['email'] = cache['email']
                            if 'name' in cache and cache['name'] and not info['display_name']:
                                info['display_name'] = cache['name']
                                
                    # Get display name from profile info
                    if not info['display_name'] and 'profile' in prefs:
                        profile_name = prefs['profile'].get('name')
                        if profile_name and not profile_name.startswith('Profile '):
                            info['display_name'] = profile_name
                    
                    # If we still don't have a display name, use a friendly version of the profile name
                    if not info['display_name']:
                        if profile_path.name == 'Default':
                            info['display_name'] = 'Default Profile'
                        elif profile_path.name.startswith('Profile '):
                            try:
                                profile_num = int(profile_path.name.split(' ')[1])
                                info['display_name'] = f'Profile {profile_num}'
                            except (IndexError, ValueError):
                                info['display_name'] = profile_path.name
                        else:
                            info['display_name'] = profile_path.name
                            
                except Exception as e:
                    logger.debug(f"Error reading profile preferences for {profile_path.name}: {e}", exc_info=True)
            
            return info
            
        except Exception as e:
            logger.warning(f"Error getting info for profile {profile_path.name}: {e}", exc_info=True)
            # Return basic info even if we can't read all details
            return {
                'name': profile_path.name,
                'path': str(profile_path),
                'size_mb': 0,
                'email': None,
                'display_name': profile_path.name,
                'last_modified': 0
            }
    
    @staticmethod
    def _get_directory_size(path: Path) -> int:
        """Calculate the total size of a directory in bytes."""
        return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())
    
    def _is_profile_directory(self, path: Path) -> bool:
        """Check if a directory is a valid Chrome profile directory."""
        # Must be a directory
        if not path.is_dir():
            return False
            
        # Must have a Preferences file or be a numbered profile
        has_prefs = (path / 'Preferences').exists()
        is_numbered_profile = path.name.startswith('Profile ') and path.name[8:].isdigit()
        is_default_profile = path.name == 'Default'
        
        return has_prefs or is_numbered_profile or is_default_profile
    
    def _discover_profiles(self) -> None:
        """Discover and categorize all available profiles in the user data directory."""
        self.profiles.clear()
        profiles_path = Path(self.user_data_dir)
        
        if not profiles_path.exists():
            logger.warning(f"Chrome user data directory not found: {profiles_path}")
            return
        
        # Find all profile directories
        for item in profiles_path.iterdir():
            # Skip special directories
            if item.name in ['.', '..'] or item.name in self.IGNORED_PROFILES:
                continue
                
            # Check if this is a profile directory
            if self._is_profile_directory(item):
                try:
                    profile_info = self._get_profile_info(item)
                    profile_info['profile_type'] = self._get_profile_type(item.name)
                    self.profiles[item.name] = profile_info
                    logger.debug(f"Found profile: {item.name} (type: {profile_info['profile_type']})")
                except Exception as e:
                    logger.warning(f"Error processing profile {item.name}: {e}", exc_info=True)
        
        # Log summary of found profiles
        logger.debug(f"Discovered {len(self.profiles)} profiles: {', '.join(self.profiles.keys())}")
    
    def list_profiles(self, profile_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available profiles, optionally filtered by type.
        
        Args:
            profile_type: Optional filter for profile type ('user', 'development', or 'system')
            
        Returns:
            List of dictionaries containing profile information
        """
        if profile_type:
            return [
                {**profile, 'name': name}
                for name, profile in self.profiles.items()
                if profile.get('profile_type') == profile_type
            ]
        return [
            {**profile, 'name': name}
            for name, profile in self.profiles.items()
        ]
        
    def get_user_profiles(self) -> List[Dict[str, Any]]:
        """Get all user profiles.
        
        Returns:
            List of user profile information dictionaries
        """
        return self.list_profiles(profile_type='user')
        
    def get_development_profiles(self) -> List[Dict[str, Any]]:
        """Get all development profiles.
        
        Returns:
            List of development profile information dictionaries
        """
        return self.list_profiles(profile_type='development')
        
    def get_system_profiles(self) -> List[Dict[str, Any]]:
        """Get all system profiles.
        
        Returns:
            List of system profile information dictionaries
        """
        return self.list_profiles(profile_type='system')
    
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


def format_size(size_mb: float) -> str:
    """Format size in MB to a human-readable string."""
    if size_mb < 1:
        return f"{size_mb * 1024:.2f} KB"
    return f"{size_mb:.2f} MB"

def select_profile_interactive(profiles: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Interactively select a profile from the list.
    
    Args:
        profiles: List of profile dictionaries from ProfileManager.list_profiles()
        
    Returns:
        Selected profile dictionary, or None if no selection made
    """
    if not profiles:
        print("No profiles found.")
        return None
    
    # Ensure all profiles have required fields
    for profile in profiles:
        profile.setdefault('display_name', profile.get('name', 'Unknown'))
        profile.setdefault('email', None)
        profile.setdefault('size_mb', 0)
        profile.setdefault('path', 'Unknown')
    
    # Sort profiles by type (user first, then development, then system)
    def get_profile_sort_key(p):
        profile_type = p.get('profile_type', 'user')
        type_order = {'user': 0, 'development': 1, 'system': 2}.get(profile_type, 3)
        return (type_order, p['display_name'].lower())
    
    profiles.sort(key=get_profile_sort_key)
    
    # Print header
    print("\n" + "="*80)
    print(f"{'#':>3}  {'Profile Name':<30} {'Email':<30} {'Size':>10}")
    print("="*80)
    
    # Print each profile
    for i, profile in enumerate(profiles, 1):
        profile['_display_index'] = i
        display_name = profile['display_name'][:28] + '..' if len(profile['display_name']) > 30 else profile['display_name']
        email = (profile['email'] or '')[:28] + '..' if profile['email'] and len(profile['email']) > 30 else (profile['email'] or '')
        size = format_size(profile['size_mb'])
        
        print(f"{i:3d}. {display_name:<30} {email:<30} {size:>10}")
    
    print("\n" + "-"*80)
    print("Profile Details (select a number to see details or press Enter to cancel):")
    
    # Main interaction loop
    while True:
        try:
            choice = input("\nSelect profile #, 'a' to show all, or press Enter to cancel: ").strip().lower()
            
            # Handle empty input (cancel)
            if not choice:
                print("Operation cancelled.")
                return None
                
            # Handle 'a' to show all profiles with full details
            if choice == 'a':
                print("\n" + "="*80)
                print("AVAILABLE PROFILES WITH DETAILS")
                print("="*80)
                
                for profile in profiles:
                    print(f"\nProfile: {profile['display_name']} ({profile['name']})")
                    if profile['email']:
                        print(f"  Email: {profile['email']}")
                    print(f"  Path: {profile['path']}")
                    print(f"  Size: {format_size(profile['size_mb'])}")
                    print(f"  Type: {profile.get('profile_type', 'user').title()}")
                
                print("\n" + "-"*80)
                continue
                
            # Handle numeric selection
            profile_index = int(choice) - 1
            if 0 <= profile_index < len(profiles):
                selected = profiles[profile_index]
                print("\n" + "="*80)
                print(f"SELECTED PROFILE: {selected['display_name']}")
                print("="*80)
                print(f"Name:    {selected['display_name']} ({selected['name']})")
                if selected['email']:
                    print(f"Email:   {selected['email']}")
                print(f"Path:    {selected['path']}")
                print(f"Size:    {format_size(selected['size_mb'])}")
                print(f"Type:    {selected.get('profile_type', 'user').title()}")
                
                confirm = input("\nUse this profile? (Y/n): ").strip().lower()
                if not confirm or confirm == 'y':
                    return selected
                continue
                
            print(f"\nInvalid selection. Please enter a number between 1 and {len(profiles)} or 'a' to show all.")
            
        except ValueError:
            print("\nPlease enter a valid number, 'a' to show all, or press Enter to cancel.")
