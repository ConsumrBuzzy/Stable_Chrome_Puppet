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
    
    def __init__(self, user_data_dir: Optional[Union[str, Path]] = None):
        """Initialize the profile manager.
        
        Args:
            user_data_dir: Optional custom path to the user data directory.
                         If not provided, will search common locations.
        """
        self.logger = logging.getLogger(__name__)
        self.user_data_dir = self._resolve_user_data_dir(user_data_dir)
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self._discover_profiles()
    
    def _resolve_user_data_dir(self, user_data_dir: Optional[Union[str, Path]] = None) -> Path:
        """Resolve the Chrome user data directory from various possible locations.
        
        Args:
            user_data_dir: Explicitly provided user data directory
            
        Returns:
            Path to the Chrome user data directory
            
        Raises:
            FileNotFoundError: If no valid Chrome user data directory could be found
        """
        # If a specific directory was provided, use it
        if user_data_dir:
            path = Path(user_data_dir).expanduser().absolute()
            if path.exists() and (path / 'Local State').exists():
                self.logger.info(f"Using provided Chrome user data directory: {path}")
                return path
            else:
                self.logger.warning(f"Provided Chrome user data directory not found or invalid: {path}")
        
        # Check known locations
        for data_dir in self.CHROME_DATA_DIRS:
            try:
                data_dir = data_dir.expanduser().absolute()
                if data_dir.exists() and (data_dir / 'Local State').exists():
                    self.logger.info(f"Found Chrome user data directory: {data_dir}")
                    return data_dir
            except Exception as e:
                self.logger.debug(f"Error checking Chrome data directory {data_dir}: {e}")
        
        # If we get here, no valid directory was found
        error_msg = (
            "Could not find Chrome user data directory. "
            "Please specify the path to your Chrome user data directory manually.\n"
            "Common locations:\n"
            "- Windows: %LOCALAPPDATA%\\Google\\Chrome\\User Data\n"
            "- Linux: ~/.config/google-chrome\n"
            "- macOS: ~/Library/Application Support/Google/Chrome"
        )
        self.logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    @staticmethod
    def get_default_user_data_dir() -> str:
        """Get the default Chrome user data directory based on the OS."""
        if os.name == 'nt':  # Windows
            # Get the actual path from the environment variable
            local_app_data = os.environ.get('LOCALAPPDATA', '')
            if not local_app_data:
                # Fallback to default path if LOCALAPPDATA is not set
                local_app_data = os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local')
            
            chrome_path = os.path.join(local_app_data, 'Google', 'Chrome', 'User Data')
            
            # Debug output
            logger.debug(f"Looking for Chrome user data in: {chrome_path}")
            
            # Check if the path exists
            if os.path.exists(chrome_path):
                logger.debug(f"Found Chrome user data directory: {chrome_path}")
                return chrome_path
            else:
                # Try alternative locations if the default doesn't exist
                alternative_paths = [
                    os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Google', 'Chrome', 'User Data'),
                    os.path.join(os.environ.get('APPDATA', ''), '..', 'Local', 'Google', 'Chrome', 'User Data'),
                    os.path.join('C:', 'Users', os.environ.get('USERNAME', ''), 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
                ]
                
                for path in alternative_paths:
                    path = os.path.abspath(path)
                    if os.path.exists(path):
                        logger.debug(f"Found Chrome user data directory (alternative path): {path}")
                        return path
                
                logger.warning(f"Chrome user data directory not found in any standard location")
                return os.path.join(local_app_data, 'Google', 'Chrome', 'User Data')
                
        elif os.name == 'posix':  # macOS/Linux
            if os.uname().sysname == 'Darwin':  # macOS
                return os.path.expanduser('~/Library/Application Support/Google/Chrome')
            return os.path.expanduser('~/.config/google-chrome')
            
        logger.warning("Unsupported operating system")
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
            - profile_type: Type of profile (user, development, system)
            - account_info: Additional account information if available
        """
        try:
            # Get basic file info
            stat_info = profile_path.stat()
            
            # Initialize info with default values
            info = {
                'name': profile_path.name,
                'path': str(profile_path.absolute()),
                'size_mb': self._get_directory_size(profile_path) / (1024 * 1024),
                'email': None,
                'emails': [],  # List to store all found emails
                'display_name': None,
                'last_modified': stat_info.st_mtime,
                'profile_type': self._get_profile_type(profile_path.name),
                'account_info': {}
            }
            
            # Set a default display name based on the profile directory name
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
            
            # Try to get additional info from preferences file
            prefs_file = profile_path / 'Preferences'
            if prefs_file.exists() and prefs_file.stat().st_size > 0:
                try:
                    with open(prefs_file, 'r', encoding='utf-8', errors='replace') as f:
                        try:
                            prefs = json.load(f)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse Preferences file {prefs_file}: {e}")
                            prefs = {}
                        
                        # Get email and name from sync account info
                        if 'profile' in prefs and 'info_cache' in prefs['profile']:
                            for account_id, cache in prefs['profile']['info_cache'].items():
                                account_email = cache.get('email')
                                if account_email:
                                    account_email = str(account_email)
                                    info['emails'].append(account_email)
                                    if not info['email']:  # Set the first email as primary
                                        info['email'] = account_email
                                
                                # Get account name if available
                                if 'name' in cache and cache['name']:
                                    name = str(cache['name'])
                                    if not info.get('display_name') or info['display_name'].startswith(('Profile ', 'Default')):
                                        info['display_name'] = name
                                    info['account_info'][account_id] = {
                                        'email': account_email,
                                        'name': name,
                                        'gaia': cache.get('gaia'),
                                        'is_consented_primary_account': cache.get('is_consented_primary_account', False)
                                    }
                        
                        # Get display name from profile info if not set yet
                        if not info.get('display_name') and 'profile' in prefs:
                            profile_name = prefs['profile'].get('name')
                            if profile_name and not str(profile_name).startswith('Profile '):
                                info['display_name'] = str(profile_name)
                        
                        # Check for accounts in the account tracker
                        if 'account_tracker' in prefs:
                            accounts = prefs.get('account_tracker', {})
                            for account_id, account in accounts.items():
                                if isinstance(account, dict) and 'account_id' in account:
                                    email = account.get('email')
                                    if email and email not in info['emails']:
                                        info['emails'].append(email)
                                        if not info['email']:
                                            info['email'] = email
                
                except Exception as e:
                    logger.warning(f"Error reading profile preferences for {profile_path.name}: {e}", exc_info=True)
            
            # Check for additional account information in other files
            try:
                # Check Web Data database for more account info
                web_data_path = profile_path / 'Web Data'
                if web_data_path.exists():
                    try:
                        import sqlite3
                        conn = sqlite3.connect(f'file:{web_data_path}?mode=ro', uri=True)
                        cursor = conn.cursor()
                        
                        # Check autofill profiles for names and emails
                        try:
                            cursor.execute('SELECT name, email FROM autofill_profiles')
                            for name, email in cursor.fetchall():
                                if email and email not in info['emails']:
                                    info['emails'].append(email)
                                    if not info['email']:
                                        info['email'] = email
                                if name and not info.get('display_name'):
                                    info['display_name'] = name
                        except sqlite3.OperationalError:
                            pass  # Table might not exist
                            
                        conn.close()
                    except Exception as e:
                        logger.debug(f"Could not read Web Data for {profile_path.name}: {e}")
            except Exception as e:
                logger.debug(f"Error checking Web Data for {profile_path.name}: {e}")
            
            # Ensure all string fields are properly encoded
            for field in ['name', 'display_name', 'email', 'path']:
                if field in info and info[field] is not None:
                    if isinstance(info[field], str):
                        info[field] = info[field].encode('utf-8', 'replace').decode('utf-8')
            
            # Clean up emails list
            info['emails'] = [str(e) for e in info['emails'] if e and isinstance(e, str)]
            
            # If we have emails but no display name, use the first part of the first email
            if not info.get('display_name') and info['emails']:
                info['display_name'] = info['emails'][0].split('@')[0].replace('.', ' ').title()
            
            return info
            
        except Exception as e:
            logger.warning(f"Error getting info for profile {profile_path.name}: {e}", exc_info=True)
            # Return basic info even if we can't read all details
            return {
                'name': str(profile_path.name),
                'path': str(profile_path.absolute()),
                'size_mb': 0,
                'email': None,
                'display_name': str(profile_path.name),
                'last_modified': 0,
                'profile_type': self._get_profile_type(profile_path.name)
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
        
        logger.debug(f"Starting profile discovery in: {profiles_path}")
        
        if not profiles_path.exists():
            error_msg = f"Chrome user data directory not found: {profiles_path}"
            logger.error(error_msg)
            print(f"\nERROR: {error_msg}")
            return
        
        try:
            # List all items in the directory for debugging
            dir_contents = list(profiles_path.iterdir())
            logger.debug(f"Found {len(dir_contents)} items in {profiles_path}")
            
            # Find all profile directories
            for item in dir_contents:
                try:
                    # Skip special directories and ignored profiles
                    if item.name in ['.', '..'] or item.name in self.IGNORED_PROFILES:
                        logger.debug(f"Skipping ignored item: {item.name}")
                        continue
                        
                    logger.debug(f"Checking item: {item.name} (is_dir: {item.is_dir()})")
                    
                    # Check if this is a profile directory
                    if self._is_profile_directory(item):
                        logger.debug(f"Processing profile directory: {item.name}")
                        try:
                            profile_info = self._get_profile_info(item)
                            profile_type = self._get_profile_type(item.name)
                            profile_info['profile_type'] = profile_type
                            self.profiles[item.name] = profile_info
                            
                            logger.info(f"Found {profile_type} profile: {item.name} "
                                     f"(display_name: {profile_info.get('display_name', 'N/A')}, "
                                     f"email: {profile_info.get('email', 'N/A')})")
                            
                        except Exception as e:
                            logger.error(f"Error getting info for profile {item.name}: {str(e)}", exc_info=True)
                            # Add basic profile info even if we can't get all details
                            self.profiles[item.name] = {
                                'name': item.name,
                                'path': str(item.absolute()),
                                'profile_type': self._get_profile_type(item.name),
                                'display_name': item.name,
                                'size_mb': 0,
                                'last_modified': 0
                            }
                    else:
                        logger.debug(f"Skipping non-profile directory: {item.name}")
                        
                except Exception as e:
                    logger.error(f"Unexpected error processing {item.name}: {str(e)}", exc_info=True)
            
            # Log summary of found profiles
            logger.info(f"Discovered {len(self.profiles)} profiles in {profiles_path}")
            for profile_name, profile in self.profiles.items():
                logger.debug(f"- {profile_name}: {profile}")
                
        except Exception as e:
            logger.critical(f"Fatal error during profile discovery: {str(e)}", exc_info=True)
            print(f"\nFATAL ERROR: Failed to discover profiles: {str(e)}")
    
    def list_profiles(self, profile_type: Optional[str] = None, include_details: bool = False) -> List[Dict[str, Any]]:
        """List all available profiles, optionally filtered by type.
        
        Args:
            profile_type: Optional filter for profile type ('user', 'development', or 'system')
            include_details: If True, include detailed account information
            
        Returns:
            List of dictionaries containing profile information
        """
        # Filter profiles by type if specified
        filtered_profiles = self.profiles.items()
        if profile_type:
            filtered_profiles = [
                (name, profile) for name, profile in filtered_profiles
                if profile.get('profile_type') == profile_type
            ]
        
        # Prepare the result list
        result = []
        for name, profile in filtered_profiles:
            # Create a copy of the profile to avoid modifying the original
            profile_info = profile.copy()
            profile_info['name'] = name
            
            # Include all emails if available
            emails = []
            if 'email' in profile_info and profile_info['email']:
                emails.append(profile_info['email'])
            if 'emails' in profile_info and profile_info['emails']:
                emails.extend([e for e in profile_info['emails'] if e and e not in emails])
            
            # Update the emails list
            if emails:
                profile_info['emails'] = emails
                profile_info['email'] = emails[0]  # Set primary email
            
            # Include account info if requested
            if not include_details:
                profile_info.pop('account_info', None)
            
            result.append(profile_info)
        
        # Sort by profile type and then by display name
        def get_sort_key(p):
            type_order = {'user': 0, 'development': 1, 'system': 2}.get(p.get('profile_type', 'user'), 3)
            return (type_order, (p.get('display_name') or p['name']).lower())
        
        return sorted(result, key=get_sort_key)
        
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
