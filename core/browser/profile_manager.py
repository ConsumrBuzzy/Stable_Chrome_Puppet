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
            Dict containing profile information
        """
        info = {
            'name': profile_path.name,
            'path': str(profile_path),
            'size_mb': self._get_directory_size(profile_path) / (1024 * 1024),
            'email': None,
            'display_name': None
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
                        if 'email' in cache:
                            info['email'] = cache['email']
                        if 'name' in cache and not info['display_name']:
                            info['display_name'] = cache['name']
                            
                # Get display name from profile info
                if not info['display_name'] and 'profile' in prefs:
                    info['display_name'] = prefs['profile'].get('name')
                    
            except Exception as e:
                logger.debug(f"Error reading profile preferences: {e}")
        
        return info
    
    @staticmethod
    def _get_directory_size(path: Path) -> int:
        """Calculate the total size of a directory in bytes."""
        return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())
    
    def _discover_profiles(self) -> None:
        """Discover and categorize all available profiles in the user data directory."""
        self.profiles.clear()
        profiles_path = Path(self.user_data_dir)
        
        if not profiles_path.exists():
            logger.warning(f"Chrome user data directory not found: {profiles_path}")
            return
        
        # Find all profile directories
        for item in profiles_path.iterdir():
            # Skip non-directories and special files
            if not item.is_dir() or item.name in ['.', '..']:
                continue
                
            # Skip ignored profiles
            if item.name in self.IGNORED_PROFILES:
                continue
                
            # Check if this is a profile directory (should contain Preferences file or be a Profile directory)
            if (item / 'Preferences').exists() or item.name.startswith('Profile '):
                try:
                    profile_info = self._get_profile_info(item)
                    profile_info['profile_type'] = self._get_profile_type(item.name)
                    self.profiles[item.name] = profile_info
                except Exception as e:
                    logger.warning(f"Error processing profile {item.name}: {e}")
                    continue
    
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
        
    # Group profiles by type
    profile_groups = {
        'user': [],
        'development': [],
        'system': []
    }
    
    for profile in profiles:
        profile_type = profile.get('profile_type', 'user')
        profile_groups[profile_type].append(profile)
    
    print("\nAvailable Chrome profiles:")
    print("-" * 40)
    
    # Display user profiles first
    if profile_groups['user']:
        print("\nUser Profiles:")
        print("-" * 40)
        for i, profile in enumerate(profile_groups['user'], 1):
            profile['_display_index'] = i
            display_name = profile.get('display_name', profile['name'])
            email = f" ({profile['email']})" if profile.get('email') else ""
            size = format_size(profile.get('size_mb', 0))
            print(f"{i:4d}. {display_name}{email}")
            print(f"      Path: {profile['path']}")
            print(f"      Size: {size}")
    
    # Display development profiles
    if profile_groups['development']:
        print("\nDevelopment Profiles:")
        print("-" * 40)
        start_idx = len(profile_groups['user']) + 1
        for i, profile in enumerate(profile_groups['development'], start_idx):
            profile['_display_index'] = i
            display_name = profile.get('display_name', profile['name'])
            size = format_size(profile.get('size_mb', 0))
            print(f"{i:4d}. {display_name}")
            print(f"      Path: {profile['path']}")
            print(f"      Size: {size}")
    
    # Display system profiles (collapsed by default)
    if profile_groups['system']:
        print("\nSystem Profiles (type 's' to show/hide):")
        if input().strip().lower() == 's':
            start_idx = len(profile_groups['user']) + len(profile_groups['development']) + 1
            for i, profile in enumerate(profile_groups['system'], start_idx):
                profile['_display_index'] = i
                size = format_size(profile.get('size_mb', 0))
                print(f"{i:4d}. {profile['name']}")
                print(f"      Path: {profile['path']}")
                print(f"      Size: {size}")
    
    # Create a flat list of all displayed profiles
    all_profiles = []
    all_profiles.extend(profile_groups['user'])
    all_profiles.extend(profile_groups['development'])
    
    # Add system profiles if they were shown
    if profile_groups['system'] and 's' in locals() and locals().get('s') == 's':
        all_profiles.extend(profile_groups['system'])
    
    while True:
        try:
            choice = input("\nEnter profile number or press Enter to cancel: ").strip()
            if not choice:
                print("\nNo profile selected.")
                return None
                
            profile_index = int(choice) - 1
            if 0 <= profile_index < len(all_profiles):
                return all_profiles[profile_index]
                
            print(f"\nInvalid selection. Please enter a number between 1 and {len(all_profiles)}.")
            
        except ValueError:
            print("\nPlease enter a valid number.")
