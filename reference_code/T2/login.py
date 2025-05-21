"""
Handles Zoom login and MFA prompt with human-like interaction patterns.
Improved error handling and logging per design plan.
@see docs/design_doc.md#12-api-and-interface-specifications
@see docs/reference.md#login
"""
from utils.config import ZOOM_SIGNIN_URL, ZOOM_USERNAME, ZOOM_PASSWORD, DEFAULT_WAIT
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from utils.logging_utils import log_info, log_error, log_debug, log_warning
from utils.exceptions import LoginError
from utils.selenium_utils import wait_for_element, wait_for_clickable, log_and_screenshot, wait_and_click
from utils.browser_utils import wait_for_page_load
from utils.human_mimic import (
    random_pause, mimic_mouse_movement, 
    mimic_typing, mimic_page_interaction, scroll_into_view
)
import time
import random
import os
from datetime import datetime
from utils.env_utils import load_credentials

def _handle_cookie_consent(driver, timeout=10):
    """Handle cookie consent banner if present."""
    try:
        # Try multiple possible selectors for cookie consent
        cookie_selectors = [
            (By.ID, "onetrust-accept-btn-handler"),  # Common consent ID
            (By.CLASS_NAME, "onetrust-close-btn-handler"),
            (By.XPATH, "//button[contains(., 'Accept') or contains(., 'Got it') or contains(., 'Agree')]"),
            (By.CSS_SELECTOR, "button[class*='cookie'], button[id*='cookie']"),
        ]
        
        for by, selector in cookie_selectors:
            try:
                cookie_btn = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((by, selector))
                )
                log_info("Found cookie consent banner, accepting...")
                mimic_mouse_movement(driver, cookie_btn)
                cookie_btn.click()
                random_pause(1, 2)  # Wait for any animations
                return True
            except (TimeoutException, NoSuchElementException):
                continue
                
    except Exception as e:
        log_debug(f"No cookie banner or error handling it: {str(e)}")
    
    return False

def _handle_google_auth_redirect(driver):
    """Handle Google OAuth redirect if present."""
    try:
        if "accounts.google.com" in driver.current_url:
            log_info("Detected Google OAuth login page")
            # Wait for email field and enter credentials
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            mimic_typing(email_field, ZOOM_USERNAME)
            
            # Click next button
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "identifierNext"))
            )
            mimic_mouse_movement(driver, next_btn)
            next_btn.click()
            
            # Handle password entry
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            random_pause(1, 2)  # Wait for password field to be ready
            
            password_field = driver.find_element(By.NAME, "password")
            mimic_typing(password_field, ZOOM_PASSWORD)
            
            # Click sign in
            signin_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "passwordNext"))
            )
            mimic_mouse_movement(driver, signin_btn)
            signin_btn.click()
            
            # Wait for redirect back to Zoom
            WebDriverWait(driver, 30).until(
                lambda d: "zoom.us" in d.current_url
            )
            return True
    except Exception as e:
        log_warning(f"Error handling Google auth: {str(e)}")
        log_and_screenshot(driver, "google_auth_error")
    return False

def _is_logged_in(driver):
    """
    Check if we're successfully logged in by checking for the profile page URL
    and other dashboard elements.
    
    Returns:
        bool: True if logged in, False otherwise
    """
    try:
        # Check if we're on the profile page (successful login)
        if "zoom.us/profile" in driver.current_url:
            log_info("Detected profile page - login successful")
            return True
            
        # First check if we're on a login page
        login_indicators = [
            (By.ID, "email"),
            (By.NAME, "email"),
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.XPATH, "//button[contains(., 'Sign In') or contains(., 'Sign in')]")
        ]
        
        # If we find any login elements, we're definitely not logged in
        for by, selector in login_indicators:
            try:
                if driver.find_elements(by, selector):
                    return False
            except:
                continue
        
        # Check for dashboard elements that indicate successful login
        dashboard_indicators = [
            (By.CLASS_NAME, "zm-avatar"),  # Profile avatar
            (By.CLASS_NAME, "zm-menu-title"),  # Menu title
            (By.CLASS_NAME, "meetings-list"),  # Meetings list
            (By.XPATH, "//*[contains(text(), 'Upcoming Meetings')]"),
            (By.CLASS_NAME, "zm-header"),  # Main header
            (By.CLASS_NAME, "zm-sidebar"),  # Sidebar menu
        ]
        
        # We need at least two indicators to be sure we're logged in
        found_indicators = 0
        for by, selector in dashboard_indicators:
            try:
                if driver.find_elements(by, selector):
                    found_indicators += 1
                    if found_indicators >= 2:  # Require at least 2 indicators
                        log_info(f"Found {found_indicators} dashboard indicators - login appears successful")
                        return True
            except Exception as e:
                log_debug(f"Error checking for dashboard element {selector}: {str(e)}")
                continue
                
        # Check URL for dashboard indicators
        if any(url in driver.current_url.lower() 
              for url in ["dashboard", "home", "meeting", "schedule"]):
            log_info("Found dashboard URL - login appears successful")
            return True
            
        # If we got here, we're not sure, so default to False
        log_debug("Could not confirm login status - defaulting to not logged in")
        return False
        
    except Exception as e:
        log_error(f"Error checking login status: {str(e)}")
        return False

def zoom_login(driver, max_retries=3):
    """
    Log in to Zoom using credentials from .env file with human-like interaction.
    Handles username, password, and MFA with improved reliability and bot detection avoidance.
    
    Args:
        driver: Selenium WebDriver instance
        max_retries: Maximum number of login attempts before giving up
        
    Raises:
        LoginError: If login fails after all retry attempts
    """
    from urllib.parse import urlparse
    import time
    
    def get_current_domain():
        """Get the current domain from the browser's URL."""
        try:
            current_url = driver.current_url
            if not current_url or current_url == 'data:,' or current_url.startswith('chrome://'):
                return None
            return urlparse(current_url).netloc.lower()
        except Exception as e:
            log_warning(f"Error getting current domain: {e}")
            return None
    
    def wait_for_domain(domains, timeout=30):
        """Wait until we're on one of the specified domains."""
        if not isinstance(domains, (list, tuple)):
            domains = [domains]
            
        log_info(f"Waiting for domain to be one of: {', '.join(domains)}")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_domain = get_current_domain()
            if current_domain and any(domain.lower() in current_domain for domain in domains):
                log_info(f"On expected domain: {current_domain}")
                return True
            time.sleep(1)
            
        log_warning(f"Timed out waiting for domains: {', '.join(domains)}")
        return False
    
    def wait_for_page_change(timeout=60, check_interval=5):
        """
        Wait for the page to change from the current URL.
        Returns True if page changed, False if timeout.
        """
        start_url = driver.current_url
        start_time = time.time()
        
        log_info(f"Waiting for page change from: {start_url}")
        
        while time.time() - start_time < timeout:
            if driver.current_url != start_url:
                log_info(f"Page changed to: {driver.current_url}")
                return True
            time.sleep(check_interval)
            
        log_warning(f"Page did not change after {timeout} seconds")
        return False
        
    def refresh_if_stalled(timeout=60):
        """Refresh the page if it hasn't changed in the specified timeout."""
        if not wait_for_page_change(timeout):
            log_warning("Page appears to be stalled - refreshing...")
            driver.refresh()
            if not wait_for_page_load(driver, 30):
                log_warning("Page load after refresh timed out")
                return False
            return True
        return True
        
    def navigate_to_url(url, expected_domains=None, timeout=30):
        """Safely navigate to a URL and verify we reached an expected domain."""
        try:
            log_info(f"Navigating to: {url}")
            driver.get(url)
            
            # Wait for page load
            if not wait_for_page_load(driver, timeout):
                log_warning("Page load verification failed, but continuing...")
                
            # If expected domains are provided, verify we're on one of them
            if expected_domains:
                if not wait_for_domain(expected_domains, timeout):
                    log_warning(f"Navigation to {url} did not result in expected domain")
                    return False
                    
            return True
            
        except Exception as e:
            log_error(f"Error navigating to {url}: {str(e)}")
            return False
    
    attempt = 0
    last_exception = None
    
    # Create screenshots directory if it doesn't exist
    os.makedirs("screenshots", exist_ok=True)
    
    while attempt < max_retries:
        try:
            attempt += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_info(f"=== Login Attempt {attempt}/{max_retries} === {timestamp}")
            
            # Load credentials
            try:
                username, password = load_credentials()
                log_debug("Successfully loaded credentials from .env")
            except Exception as e:
                log_error(f"Failed to load credentials: {e}")
                raise LoginError(f"Failed to load credentials: {e}")
            
            # Navigate to Zoom sign-in page with human-like delay
            log_info("Navigating to Zoom sign-in page...")
            if not navigate_to_url(ZOOM_SIGNIN_URL, expected_domains=["zoom.us"], timeout=30):
                log_warning("Failed to navigate to Zoom sign-in page")
                continue
                
            # Additional verification that we're on the login page
            try:
                # Try multiple selectors with separate waits
                try:
                    WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located((By.ID, "email"))
                    )
                except TimeoutException:
                    WebDriverWait(driver, 3).until(
                        EC.visibility_of_element_located((By.NAME, "email"))
                    )
                log_info("Successfully loaded login page")
            except TimeoutException:
                log_warning("Login page elements not found after navigation")
                
            random_pause(2, 4)  # Human-like delay after page load
            
            # Check if already logged in
            if _is_logged_in(driver):
                log_info("Already logged in to Zoom")
                return True
            
            # Handle cookie consent if present
            _handle_cookie_consent(driver)
            
            # Handle Google OAuth redirect if present
            if "accounts.google.com" in driver.current_url:
                if _handle_google_auth_redirect(driver):
                    log_info("Successfully completed Google OAuth login")
                    return True
            
            # Perform random page interaction to appear more human
            mimic_page_interaction(driver)
            
            # Wait for email field to be present and visible
            try:
                log_info("Waiting for login form...")
                if not refresh_if_stalled():
                    log_warning("Page appears to be unresponsive, continuing with refresh...")
                    continue
                    
                log_info("Processing email field...")
                # Try multiple selectors for email field
                email_selectors = [
                    (By.ID, "email"),
                    (By.NAME, "email"),
                    (By.CSS_SELECTOR, "input[type='email']"),
                    (By.XPATH, "//input[contains(@class, 'email') or contains(@id, 'email')]")
                ]
                
                email_field = None
                for by, selector in email_selectors:
                    try:
                        email_field = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((by, selector))
                        )
                        break
                    except:
                        continue
                
                if not email_field:
                    raise NoSuchElementException("Could not find email field with any selector")
                
                # Scroll to field and clear any existing text with human-like backspacing
                scroll_into_view(driver, email_field)
                email_field.clear()
                random_pause(0.3, 0.7)
                
                # Move mouse to field and type with human-like behavior
                mimic_mouse_movement(driver, email_field)
                mimic_typing(email_field, username)
                log_debug("Email entered")
                
            except Exception as e:
                log_error(f"Failed to enter email: {e}")
                log_and_screenshot(driver, f"email_entry_failed_{timestamp}")
                raise LoginError(f"Email entry failed: {e}")
            
            # Handle password input with human-like interaction
            try:
                log_info("Processing password field...")
                # Try multiple selectors for password field
                password_selectors = [
                    (By.ID, "password"),
                    (By.NAME, "password"),
                    (By.CSS_SELECTOR, "input[type='password']"),
                    (By.XPATH, "//input[contains(@class, 'password') or contains(@id, 'password')]")
                ]
                
                password_field = None
                for by, selector in password_selectors:
                    try:
                        password_field = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((by, selector))
                        )
                        break
                    except:
                        continue
                
                if not password_field:
                    raise NoSuchElementException("Could not find password field with any selector")
                
                # Move mouse to field and type with human-like behavior
                scroll_into_view(driver, password_field)
                mimic_mouse_movement(driver, password_field)
                random_pause(0.2, 0.5)
                mimic_typing(password_field, password)
                log_debug("Password entered")
                
            except Exception as e:
                log_error(f"Failed to enter password: {e}")
                log_and_screenshot(driver, f"password_entry_failed_{timestamp}")
                raise LoginError(f"Password entry failed: {e}")
            
            # Click sign in button with human-like interaction
            try:
                log_info("Attempting to sign in...")
                
                # Check for page stall before proceeding
                if not refresh_if_stalled():
                    log_warning("Page appears to be unresponsive after email/password entry")
                    continue
                    
                # Try multiple selectors for sign in button
                signin_selectors = [
                    (By.XPATH, "//button[@type='submit']"),
                    (By.CSS_SELECTOR, "button[type='submit']"),
                    (By.CLASS_NAME, "signin"),
                    (By.ID, "signin"),
                    (By.XPATH, "//button[contains(., 'Sign In') or contains(., 'Sign in')]")
                ]
                
                signin_button = None
                for by, selector in signin_selectors:
                    try:
                        signin_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        break
                    except:
                        continue
                
                if not signin_button:
                    raise NoSuchElementException("Could not find sign in button with any selector")
                
                # Scroll to button and add human-like delay
                scroll_into_view(driver, signin_button)
                random_pause(0.5, 1.5)
                
                # Move mouse to button and click
                mimic_mouse_movement(driver, signin_button)
                random_pause(0.3, 0.8)
                signin_button.click()
                log_debug("Sign in button clicked")
                
            except ElementClickInterceptedException:
                # If button is covered by another element, try JavaScript click
                try:
                    driver.execute_script("arguments[0].click();", signin_button)
                    log_debug("Used JavaScript click for sign in button")
                except Exception as e:
                    log_error(f"JavaScript click also failed: {e}")
                    raise
            except Exception as e:
                log_error(f"Failed to click sign in button: {e}")
                log_and_screenshot(driver, f"signin_button_click_failed_{timestamp}")
                raise LoginError(f"Sign in button click failed: {e}")
            
            # Handle MFA if required
            try:
                log_info("Checking for MFA requirement...")
                
                # Check for MFA input field first (in case we're already on the MFA page)
                mfa_selectors = [
                    (By.NAME, "code"),
                    (By.ID, "verificationCode"),
                    (By.CSS_SELECTOR, "input[type='text'][placeholder*='code']"),
                    (By.XPATH, "//input[contains(@name, 'code') or contains(@id, 'code')]"),
                    (By.XPATH, "//input[@type='text' and contains(@class, 'verification-code')]")
                ]
                
                mfa_prompt = None
                for by, selector in mfa_selectors:
                    try:
                        mfa_prompt = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((by, selector))
                        )
                        log_info("Found MFA input field")
                        break
                    except:
                        continue
                
                # Check if we're on the MFA verification help page or have the MFA prompt
                if "/signin/otp/verify_help" in driver.current_url or mfa_prompt:
                    log_info("MFA verification required...")
                    
                    if "/signin/otp/verify_help" in driver.current_url:
                        log_info("Detected MFA verification help page")
                        log_info("Please complete the MFA verification in the browser...")
                        
                        # Wait for user to complete MFA
                        try:
                            WebDriverWait(driver, 300).until(  # 5 minute timeout for MFA
                                lambda d: "/signin/otp/verify_help" not in d.current_url
                            )
                            log_info("MFA verification appears to be complete")
                            
                            # After MFA, wait for navigation to complete
                            WebDriverWait(driver, 30).until(
                                lambda d: d.current_url != "about:blank" and 
                                        not d.current_url.startswith("https://zoom.us/signin")
                            )
                            
                            # Add a small delay to ensure page is fully loaded
                            time.sleep(2)
                            
                        except TimeoutException:
                            log_warning("Timed out waiting for MFA verification")
                            log_and_screenshot(driver, "mfa_verification_timeout")
                
                if mfa_prompt:
                    log_info("MFA verification required...")
                    print("\n" + "="*50)
                    print("MFA VERIFICATION REQUIRED")
                    print("="*50)
                    print("Please check your authentication app or email for the verification code.")
                    print("Enter the code below when prompted.\n")
                    
                    while True:
                        try:
                            code = input("Enter MFA code (or 'resend' to request a new code): ").strip()
                            
                            if code.lower() == 'resend':
                                # Try to find and click resend code link
                                resend_selectors = [
                                    (By.LINK_TEXT, "Resend code"),
                                    (By.XPATH, "//a[contains(., 'Resend') and contains(., 'code')]")
                                ]
                                resend_clicked = False
                                for by, selector in resend_selectors:
                                    try:
                                        resend_link = WebDriverWait(driver, 5).until(
                                            EC.element_to_be_clickable((by, selector))
                                        )
                                        mimic_mouse_movement(driver, resend_link)
                                        resend_link.click()
                                        log_info("Requested new MFA code")
                                        print("New code requested. Please check your device.")
                                        resend_clicked = True
                                        break
                                    except:
                                        continue
                                if not resend_clicked:
                                    print("Could not find resend code option. Please try again.")
                                continue
                                
                            if not code.isdigit() or len(code) < 6:
                                print("Invalid code. Please enter a 6+ digit number or 'resend'.")
                                continue
                                
                            break
                                
                        except KeyboardInterrupt:
                            print("\nMFA entry cancelled.")
                            raise LoginError("MFA verification cancelled by user")
                    
                    # Enter MFA code with human-like typing
                    scroll_into_view(driver, mfa_prompt)
                    mimic_mouse_movement(driver, mfa_prompt)
                    random_pause(0.3, 0.7)
                    mimic_typing(mfa_prompt, code)
                    random_pause(0.5, 1.0)
                    
                    # Click verify button
                    verify_buttons = [
                        (By.XPATH, "//button[contains(., 'Verify') or contains(., 'Submit')]"),
                        (By.CSS_SELECTOR, "button[type='submit']"),
                        (By.ID, "verify"),
                        (By.CLASS_NAME, "verify"),
                        (By.XPATH, "//button[contains(., 'Continue')]")
                    ]
                    
                    verify_button = None
                    for by, selector in verify_buttons:
                        try:
                            verify_button = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((by, selector))
                            )
                            break
                        except:
                            continue
                    
                    if verify_button:
                        mimic_mouse_movement(driver, verify_button)
                        random_pause(0.3, 0.7)
                        verify_button.click()
                        log_info("MFA code submitted")
                        
                        # Wait for MFA verification to complete
                        try:
                            WebDriverWait(driver, 30).until(
                                lambda d: "/signin/otp/verify_help" not in d.current_url and 
                                        not any(x[1] in driver.page_source.lower() for x in [
                                            ("incorrect code"), ("invalid code"), ("try again")])
                            )
                        except TimeoutException:
                            log_warning("MFA verification may have failed. Please check for error messages.")
                            log_and_screenshot(driver, "mfa_verification_issue")
                    else:
                        log_warning("Could not find verify button, trying to submit form")
                        mfa_prompt.send_keys(Keys.RETURN)
                        
                        # Wait for MFA verification to complete and navigate to profile page
                        try:
                            WebDriverWait(driver, 30).until(
                                lambda d: "/signin/otp/verify_help" not in d.current_url and 
                                        not any(x[1] in driver.page_source.lower() for x in [
                                            ("incorrect code"), ("invalid code"), ("try again")])
                            )
                            log_info("MFA verification appears to be complete")
                            
                            # Navigate to profile page
                            profile_icon_selectors = [
                                (By.CLASS_NAME, "zm-avatar"),
                                (By.CSS_SELECTOR, "[aria-label*='Profile']"),
                                (By.XPATH, "//a[contains(@href, '/profile')]")
                            ]
                            
                            for by, selector in profile_icon_selectors:
                                try:
                                    profile_icon = WebDriverWait(driver, 5).until(
                                        EC.element_to_be_clickable((by, selector))
                                    )
                                    mimic_mouse_movement(driver, profile_icon)
                                    profile_icon.click()
                                    log_info("Clicked profile icon")
                                    break
                                except:
                                    continue
                                    
                            # Wait for profile page to load
                            WebDriverWait(driver, 10).until(
                                lambda d: "zoom.us/profile" in d.current_url
                            )
                        except Exception as nav_error:
                            log_warning(f"Could not navigate to profile page: {nav_error}")
                            # Continue if we can't navigate to profile but are logged in
                        
            except Exception as e:
                log_debug(f"No MFA required or MFA handling skipped: {e}")
                # Not an error - MFA might not be required
                pass
            
            # Verify successful login by checking for profile page
            try:
                log_info("Verifying login status and waiting for profile page...")
                
                # Wait for either the profile page or dashboard indicators
                WebDriverWait(driver, 30).until(
                    lambda d: _is_logged_in(d)
                )
                
                log_info("✓ Successfully logged in to Zoom and verified profile page")
                log_and_screenshot(driver, "login_successful")
                return True
                
            except TimeoutException:
                # Check for login failure indicators
                page_source = driver.page_source.lower()
                error_indicators = [
                    "incorrect", "error", "invalid", "wrong", "try again",
                    "unable to sign in", "sign in failed", "login failed"
                ]
                
                if any(text in page_source for text in error_indicators):
                    error_msg = "Login failed: Incorrect credentials or error on page"
                    log_error(error_msg)
                    log_and_screenshot(driver, f"login_failed_{timestamp}")
                    raise LoginError(error_msg)
                
                # If we got here, the login might still be in progress
                log_warning("Login verification timeout. Checking if we're logged in...")
                if _is_logged_in(driver):
                    log_info("✓ Successfully logged in to Zoom (verified via page check)")
                    log_and_screenshot(driver, "login_successful")
                    return True
                
                # If we're still not logged in, raise an exception
                raise LoginError("Login verification failed: Could not confirm successful login - profile page not reached")
                
        except Exception as e:
            last_exception = e
            log_warning(f"Login attempt {attempt} failed: {str(e)}")
            
            if attempt < max_retries:
                retry_delay = random.uniform(3, 8)  # Random delay between retries
                log_info(f"Retrying in {retry_delay:.1f} seconds...")
                time.sleep(retry_delay)
            
            # Take a screenshot of the current state for debugging
            log_and_screenshot(driver, f"login_attempt_{attempt}_failed_{timestamp}")
    
    # If we've exhausted all retry attempts
    error_msg = f"All {max_retries} login attempts failed"
    log_error(error_msg)
    if last_exception:
        log_error(f"Last error: {str(last_exception)}")
    log_and_screenshot(driver, f"all_login_attempts_failed_{timestamp}")
    raise LoginError(error_msg)
