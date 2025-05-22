"""
Profile class for managing browser profiles.

This module provides a Profile class that represents a browser profile
and provides methods for managing its state and configuration.
"""
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class Profile:
    """Represents a browser profile with its configuration and state."""
    
    def __init__(self, name: str, path: Path, is_default: bool = False):
        """Initialize a Profile instance.
        
        Args:
            name: Name of the profile
            path: Path to the profile directory
            is_default: Whether this is the default profile
        """
        self.name = name
        self.path = Path(path).absolute()
        self.is_default = is_default
        self._size_mb: Optional[float] = None
    
    def __str__(self) -> str:
        """String representation of the profile."""
        return f"Profile(name='{self.name}', path='{self.path}')"
    
    def __repr__(self) -> str:
        """Official string representation of the profile."""
        return f"<Profile '{self.name}'>"
    
    @property
    def size_mb(self) -> float:
        """Get the size of the profile directory in MB."""
        if self._size_mb is None:
            self._size_mb = self._get_directory_size_mb(self.path)
        return self._size_mb
    
    def validate(self) -> Tuple[bool, str]:
        """Validate if the profile is accessible and valid.
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not self.path.exists():
            return False, f"Profile directory does not exist: {self.path}"
            
        if not self.path.is_dir():
            return False, f"Profile path is not a directory: {self.path}"
            
        return True, f"Profile '{self.name}' is valid"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the profile to a dictionary.
        
        Returns:
            Dictionary containing profile information
        """
        return {
            'name': self.name,
            'path': str(self.path),
            'is_default': self.is_default,
            'size_mb': self.size_mb,
            'is_valid': self.validate()[0]
        }
    
    @staticmethod
    def _get_directory_size_mb(directory: Path) -> float:
        """Calculate the size of a directory in MB.
        
        Args:
            directory: Path to the directory
            
        Returns:
            Size in MB as float
        """
        try:
            total_size = sum(
                f.stat().st_size 
                for f in directory.glob('**/*') 
                if f.is_file()
            )
            return round(total_size / (1024 * 1024), 2)  # Convert to MB
        except Exception as e:
            logger.warning(f"Could not calculate size for {directory}: {e}")
            return 0.0
    
    def copy_to(self, destination: Path) -> 'Profile':
        """Create a copy of this profile at the specified destination.
        
        Args:
            destination: Path to copy the profile to
            
        Returns:
            New Profile instance for the copied profile
        """
        if not destination.exists():
            destination.mkdir(parents=True)
            
        # Copy all files and directories recursively
        shutil.copytree(
            self.path,
            destination / self.path.name,
            dirs_exist_ok=True
        )
        
        return Profile(
            name=f"{self.name}_copy",
            path=destination / self.path.name,
            is_default=False
        )
