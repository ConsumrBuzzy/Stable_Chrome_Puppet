"""
ChromeDriver management utilities for automatic installation and version management.
"""
import logging
import os
import platform
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Optional, Tuple
import requests
from urllib.parse import urljoin

class ChromeDriverManager:
    """
    Manages ChromeDriver installation and version management.
    
    This class handles automatic downloading, installation, and version
    matching of ChromeDriver for the installed Chrome browser.
    """
    
    CHROME_VERSION_URL = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
    CHROME_DRIVER_BASE_URL = "https://chromedriver.storage.googleapis.com"
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the ChromeDriver manager."""
        self.logger = logger or logging.getLogger(__name__)
        self.platform = self._get_platform()
        self.chrome_version = self._get_chrome_version()
        
    def _get_platform(self) -> str:
        """Get the current platform identifier for ChromeDriver downloads."""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == 'windows':
            return 'win32'  # ChromeDriver for Windows is 32-bit but works on 64-bit
        elif system == 'darwin':
            return 'mac64' if machine == 'x86_64' or machine == 'arm64' else 'mac64_m1'
        elif system == 'linux':
            return 'linux64'
        else:
            raise OSError(f"Unsupported platform: {system} {machine}")
    
    def _get_chrome_version(self) -> str:
        """Get the installed Chrome/Chromium version."""
        try:
            if platform.system() == 'Windows':
                # Windows registry approach
                cmd = 'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version'
                self.logger.debug(f"Running command: {cmd}")
                result = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.PIPE)
                version = re.search(r'\d+\.\d+\.\d+\.\d+', result)
                if version:
                    return version.group(0)
            else:
                # macOS/Linux approach
                for cmd in ['google-chrome --version', 'chromium-browser --version', 'google-chrome-stable --version']:
                    try:
                        result = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.PIPE)
                        version = re.search(r'\d+\.\d+\.\d+\.\d+', result)
                        if version:
                            return version.group(0)
                    except subprocess.CalledProcessError:
                        continue
        except Exception as e:
            self.logger.warning(f"Could not determine Chrome version: {e}")
            
        # Fallback to latest stable ChromeDriver version
        try:
            response = requests.get(self.CHROME_VERSION_URL, timeout=10)
            response.raise_for_status()
            return response.text.strip()
        except Exception as e:
            raise RuntimeError(f"Could not determine Chrome version: {e}")
    
    def get_matching_chromedriver_version(self) -> str:
        """Get the ChromeDriver version that matches the installed Chrome version."""
        try:
            # First try to get the exact version match
            version_url = f"{self.CHROME_VERSION_URL}_{self.chrome_version}"
            response = requests.get(version_url, timeout=10)
            response.raise_for_status()
            return response.text.strip()
        except requests.RequestException:
            try:
                # If exact version fails, try with just major version
                major_version = self.chrome_version.split('.')[0]
                version_url = f"{self.CHROME_VERSION_URL}_{major_version}"
                response = requests.get(version_url, timeout=10)
                response.raise_for_status()
                return response.text.strip()
            except requests.RequestException as e:
                # If all else fails, try to get the latest version
                try:
                    self.logger.warning(f"Could not find matching ChromeDriver version, trying latest: {e}")
                    response = requests.get(self.CHROME_VERSION_URL, timeout=10)
                    response.raise_for_status()
                    return response.text.strip()
                except requests.RequestException as e:
                    self.logger.error(f"Failed to get ChromeDriver version: {e}")
                    return "114.0.5735.90"  # Fallback to a known working version
    
    def get_driver_url(self, version: str) -> str:
        """Get the download URL for ChromeDriver."""
        # ChromeDriver URLs follow this pattern:
        # https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_win32.zip
        # For Chrome 115 and above, the format is:
        # https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/115.0.5790.98/win64/chromedriver-win64.zip
        
        # First, try to parse the version
        try:
            major_version = int(version.split('.')[0])
            
            # For Chrome 115 and above
            if major_version >= 115:
                # Try the new Chrome for Testing URL format
                filename = f"chromedriver-{self.platform}.zip"
                return f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{version}/{self.platform}/{filename}"
            
            # For older versions
            filename = f"chromedriver_{self.platform}.zip"
            return f"{self.CHROME_DRIVER_BASE_URL}/{version}/{filename}"
            
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Error parsing version {version}, using fallback URL: {e}")
            # Fallback to a known working version
            return "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_win32.zip"
    
    def download_driver(self, url: str, target_path: Path) -> None:
        """Download and extract ChromeDriver."""
        try:
            # Create target directory if it doesn't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download the file
            self.logger.info(f"Downloading ChromeDriver from {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save the zip file
            zip_path = target_path.with_suffix('.zip')
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract the zip file
            self.logger.info(f"Extracting ChromeDriver to {target_path.parent}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_path.parent)
            
            # Make the driver executable (Unix-like systems)
            if platform.system() != 'Windows':
                os.chmod(target_path, 0o755)
            
            # Clean up the zip file
            zip_path.unlink()
            
            self.logger.info(f"Successfully installed ChromeDriver to {target_path}")
            
        except Exception as e:
            if target_path.exists():
                target_path.unlink()
            raise RuntimeError(f"Failed to download ChromeDriver: {e}")
    
    def setup_chromedriver(self, target_dir: Optional[Path] = None) -> Path:
        """Set up ChromeDriver, downloading it if necessary."""
        # Determine target directory
        if target_dir is None:
            target_dir = Path.home() / ".chromedriver"
        
        # Create target directory if it doesn't exist
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine ChromeDriver version
        version = self.get_matching_chromedriver_version()
        
        # Determine platform-specific driver name
        driver_name = "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
        driver_path = target_dir / version / driver_name
        
        # Return if driver already exists
        if driver_path.exists():
            self.logger.debug(f"Using existing ChromeDriver at {driver_path}")
            return driver_path
        
        # Download and extract ChromeDriver
        driver_url = self.get_driver_url(version)
        self.download_driver(driver_url, driver_path)
        
        return driver_path

def ensure_chromedriver_available() -> str:
    """
    Ensure ChromeDriver is available, downloading it if necessary.
    
    Returns:
        str: Path to the ChromeDriver executable
    """
    try:
        manager = ChromeDriverManager()
        driver_path = manager.setup_chromedriver()
        return str(driver_path)
    except Exception as e:
        raise RuntimeError(f"Failed to set up ChromeDriver: {e}")
