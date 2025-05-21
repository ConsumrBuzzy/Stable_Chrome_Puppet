"""
Authentication module for DNC Genie.
Handles login, MFA, and session management.
"""
import time
from typing import Optional, Dict, Any, Tuple
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    ElementClickInterceptedException, WebDriverException
)

from config import settings
from session import session
from exceptions import (
    AuthenticationError, MFANotSupportedError,
    ElementNotFoundError, TimeoutError as DNCGenieTimeoutError
)
from selenium_utils import (
    wait_for_element, wait_for_clickable,
    safe_click, log_and_screenshot
)
from logging_utils import log_info, log_warning, log_error, log_debug

class ZoomAuthenticator:
    """Handles Zoom authentication flow including MFA."""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.timeout = settings.IMPLICIT_WAIT
    
    def login(self, username: str, password: str) -> bool:
        """
        Perform Zoom login with credentials.
        
        Args:
            username: Zoom username/email
            password: Zoom password
            
        Returns:
            bool: True if login was successful
            
        Raises:
            AuthenticationError: If login fails
        """
        try:
            log_info("Navigating to Zoom login page...")
            self.driver.get(settings.ZOOM_SIGNIN_URL)
            
            # Handle cookie consent if present
            self._handle_cookie_consent()
            
            # Enter credentials
            log_info("Entering credentials...")
            self._enter_credentials(username, password)
            
            # Handle MFA if required
            if self._is_mfa_required():
                log_info("MFA required, processing...")
                self._handle_mfa()
            
            # Wait for successful login
            if not self._wait_for_login_success():
                raise AuthenticationError("Failed to verify login success")
            
            # Create session
            session.create_session({
                "email": username,
                # In a real implementation, we'd get these from the auth response
                "user_id": "current_user",
                "token": "dummy_token",
                "refresh_token": "dummy_refresh_token"
            })
            
            log_info("Login successful")
            return True
            
        except Exception as e:
            log_error(f"Login failed: {str(e)}")
            session.invalidate()
            raise AuthenticationError(f"Login failed: {str(e)}")
    
    def _handle_cookie_consent(self) -> None:
        """Handle cookie consent banner if present."""
        try:
            # Try different selectors for cookie consent
            cookie_selectors = [
                (By.ID, "onetrust-accept-btn-handler"),
                (By.CLASS_NAME, "onetrust-close-btn-handler"),
                (By.XPATH, "//button[contains(., 'Accept') or contains(., 'Got it') or contains(., 'Agree')]"),
            ]
            
            for by, selector in cookie_selectors:
                try:
                    btn = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    log_info("Accepting cookie consent...")
                    safe_click(self.driver, btn)
                    time.sleep(1)  # Wait for any animations
                    return
                except (TimeoutException, NoSuchElementException):
                    continue
                    
        except Exception as e:
            log_warning(f"Error handling cookie consent: {str(e)}")
    
    def _enter_credentials(self, username: str, password: str) -> None:
        """Enter username and password into the login form."""
        try:
            # Wait for and fill username
            email_field = wait_for_element(
                self.driver,
                (By.ID, "email"),
                timeout=self.timeout
            )
            email_field.clear()
            email_field.send_keys(username)
            
            # Fill password
            password_field = wait_for_element(
                self.driver,
                (By.ID, "password"),
                timeout=self.timeout
            )
            password_field.clear()
            password_field.send_keys(password)
            
            # Click sign in button
            signin_button = wait_for_clickable(
                self.driver,
                (By.CSS_SELECTOR, "button[type='submit']"),
                timeout=self.timeout
            )
            safe_click(self.driver, signin_button)
            
        except TimeoutException as e:
            log_and_screenshot(self.driver, "login_form_timeout")
            raise ElementNotFoundError("Could not find login form elements") from e
    
    def _is_mfa_required(self) -> bool:
        """Check if MFA is required."""
        try:
            # Look for MFA input or verification code field
            return bool(wait_for_element(
                self.driver,
                (By.CSS_SELECTOR, "input[name*='code'], input[type*='code']"),
                timeout=5,
                raise_exception=False
            ))
        except Exception:
            return False
    
    def _handle_mfa(self) -> None:
        """Handle MFA verification."""
        # In a real implementation, this would integrate with an MFA provider
        # or prompt the user for the code
        raise MFANotSupportedError("MFA is not supported in this version")
    
    def _wait_for_login_success(self, timeout: int = 30) -> bool:
        """Wait for successful login by checking for dashboard elements."""
        try:
            # Wait for URL to change from login page
            WebDriverWait(self.driver, timeout).until(
                lambda d: "signin" not in d.current_url.lower()
            )
            
            # Check for dashboard elements
            dashboard_indicators = [
                (By.CLASS_NAME, "dashboard-container"),
                (By.ID, "dashboard"),
                (By.XPATH, "//*[contains(text(), 'Dashboard')]")
            ]
            
            for by, selector in dashboard_indicators:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    return True
                except TimeoutException:
                    continue
            
            # If we got this far, we might be on the dashboard but couldn't find indicators
            # Check URL as a fallback
            return "dashboard" in self.driver.current_url.lower()
            
        except TimeoutException as e:
            log_and_screenshot(self.driver, "login_timeout")
            raise DNCGenieTimeoutError("Timeout waiting for login to complete") from e
        except Exception as e:
            log_error(f"Error verifying login success: {str(e)}")
            return False

def zoom_login(driver: WebDriver, username: str, password: str) -> None:
    """
    High-level login function that uses the ZoomAuthenticator.
    
    Args:
        driver: Selenium WebDriver instance
        username: Zoom username/email
        password: Zoom password
        
    Raises:
        AuthenticationError: If login fails
    """
    authenticator = ZoomAuthenticator(driver)
    try:
        authenticator.login(username, password)
        # Save session after successful login
        session.authenticate("zoom_auth_token", 3600)  # 1 hour token
    except Exception as e:
        log_error(f"Login failed: {str(e)}")
        raise AuthenticationError(f"Login failed: {str(e)}")
