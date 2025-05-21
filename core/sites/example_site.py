"""
Example implementation of a site handler.

This module shows how to implement a site handler for a specific website
by subclassing BaseSiteHandler.
"""
import time
from typing import Optional, Dict, Any
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException
)

from .base_site import BaseSiteHandler
from ..browser.chrome import ChromeBrowser
from ..config import ChromeConfig
from ..utils import retry_on_exception


class ExampleSiteHandler(BaseSiteHandler):
    """Handler for example.com website.
    
    This is an example implementation showing how to create a site handler
    for a specific website.
    """
    
    LOGIN_URL = "https://example.com/login"
    DASHBOARD_URL = "https://example.com/dashboard"
    
    def get_site_name(self) -> str:
        return "example_com"
    
    def get_base_url(self) -> str:
        return "https://example.com"
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in by looking for user menu or dashboard elements."""
        if not self.browser or not self.browser.is_running():
            return False
            
        try:
            # Try to find an element that only exists when logged in
            self.browser.driver.find_element(By.ID, "user-menu")
            return True
        except NoSuchElementException:
            return False
    
    @retry_on_exception(max_retries=2, exceptions=(TimeoutException, WebDriverException))
    def login(self, username: str, password: str, **kwargs) -> bool:
        """Log in to the example.com website.
        
        Args:
            username: Login username or email
            password: Login password
            **kwargs: Additional arguments like 'remember_me'
            
        Returns:
            bool: True if login was successful
        """
        self.start_browser()
        
        try:
            # Navigate to login page
            self.browser.navigate_to(self.LOGIN_URL)
            
            # Fill in login form
            username_field = self.browser.driver.find_element(By.NAME, "username")
            password_field = self.browser.driver.find_element(By.NAME, "password")
            
            username_field.clear()
            username_field.send_keys(username)
            
            password_field.clear()
            password_field.send_keys(password)
            
            # Handle remember me checkbox if needed
            if kwargs.get('remember_me', True):
                remember_me = self.browser.driver.find_element(By.NAME, "remember")
                if not remember_me.is_selected():
                    remember_me.click()
            
            # Submit the form
            login_button = self.browser.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete and redirect
            time.sleep(2)  # Simple wait - in production, use WebDriverWait
            
            # Verify login was successful
            if self.is_logged_in():
                # Save cookies for future sessions
                self.save_cookies()
                return True
                
            return False
            
        except Exception as e:
            print(f"Login failed: {e}")
            # Take a screenshot for debugging
            self.browser.take_screenshot(str(self.data_dir / 'login_error.png'))
            return False
    
    def logout(self) -> None:
        """Log out of the example.com website."""
        if not self.browser or not self.browser.is_running():
            return
            
        try:
            # Navigate to logout URL or click logout button
            self.browser.navigate_to(f"{self.get_base_url()}/logout")
            
            # Or find and click the logout button
            # logout_button = self.browser.driver.find_element(By.LINK_TEXT, "Logout")
            # logout_button.click()
            
            # Wait for logout to complete
            time.sleep(1)
            
            # Delete cookies file if it exists
            cookies_file = self.data_dir / 'cookies.pkl'
            if cookies_file.exists():
                cookies_file.unlink()
                
        except Exception as e:
            print(f"Error during logout: {e}")
    
    # Add site-specific methods below
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Example method to get data from the dashboard."""
        if not self.is_logged_in():
            raise RuntimeError("Not logged in")
            
        self.browser.navigate_to(self.DASHBOARD_URL)
        
        # Example: Extract data from the dashboard
        data = {
            'username': self.browser.driver.find_element(By.CLASS_NAME, 'username').text,
            'stats': {}
        }
        
        # Add more data extraction as needed
        
        return data
