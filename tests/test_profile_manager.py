import os
import sys
import json
import logging
from pathlib import Path
from unittest import TestCase, mock

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.browser.profile_manager import ProfileManager, ProfileInfo

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestProfileManager(TestCase):    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ProfileManager()
        
    def test_get_profile_info(self):
        """Test getting profile information."""
        # Get the first available profile
        profiles = self.manager.list_profiles()
        if not profiles:
            self.skipTest("No Chrome profiles found")
            
        # Test with the first profile
        profile_name = next(iter(profiles.keys()))
        profile_path = self.manager.get_profile_path(profile_name)
        
        self.assertIsNotNone(profile_path)
        self.assertTrue(profile_path.exists())
        
        # Get detailed profile info
        profile_info = self.manager._get_profile_info(profile_path)
        
        # Basic assertions
        self.assertIsInstance(profile_info, dict)
        self.assertEqual(profile_info['name'], profile_path.name)
        self.assertTrue(profile_info['is_valid'])
        
        # Log the profile info for inspection
        logger.info("Profile info: %s", json.dumps(profile_info, indent=2, default=str))
        
    def test_list_profiles(self):
        """Test listing all profiles."""
        profiles = self.manager.list_profiles(include_details=True)
        self.assertIsInstance(profiles, dict)
        
        # Log the profiles for inspection
        logger.info("Found %d profiles", len(profiles))
        for name, info in profiles.items():
            logger.info("Profile '%s': %s", name, json.dumps(info, indent=2, default=str))

if __name__ == "__main__":
    import unittest
    unittest.main()
