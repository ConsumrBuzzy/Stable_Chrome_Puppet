"""
zoom_login.py
Dedicated Zoom login automation module, with robust error/retry handling for network errors.
Ported and enhanced from ZoomDNCGenie.py and user feedback.
"""
import time
from utils.logging_utils import log_info, log_warning, log_error
from config import ZOOM_SIGNIN_URL, EMAIL_INPUT_ID, PASSWORD_INPUT_ID, SIGN_IN_BTN_ID, RECAPTCHA_ERROR_SELECTOR, MAX_LOGIN_RETRIES, LOGIN_WAIT
from utils.exceptions import ZoomLoginFailedException, CaptchaDetectedException, ElementNotFoundException
from utils.selenium_utils import wait_for_element, wait_for_clickable, wait_for_element_or_url, wait_and_fill, wait_and_click, log_and_screenshot
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Any

# Configurable login wait constants
# LOGIN_RESULT_WAIT: Maximum time (seconds) to wait for login to succeed before retrying. Reduce for faster failure detection.
LOGIN_RESULT_WAIT = 45  # seconds (shortened for faster login polling)
LOGIN_POLL_INTERVAL = 2  # seconds

def save_html(driver, tag):
    """Save the current page HTML to shots/<tag>_<timestamp>.html for diagnostics."""
    import os, datetime
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    html_dir = os.path.join(os.getcwd(), 'shots')
    os.makedirs(html_dir, exist_ok=True)
    fname = os.path.join(html_dir, f'{tag}_{ts}.html')
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)


def zoom_login(driver: Any, email: str, password: str, max_retries: int = MAX_LOGIN_RETRIES) -> bool:
    """
    Log in to Zoom.us using provided credentials.
    Tries 3 times, then refreshes and tries 3 more. Aborts after 6 total failures.
    Returns True if login successful, False otherwise.
    """
    def attempt_login_batch(batch_num: int) -> bool:
        attempt = 0
        while attempt < max_retries:
            try:
                log_info(f"[Zoom Genie] Batch {batch_num} Attempt {attempt+1}/{max_retries} - Current URL: {driver.current_url}")
                log_info('[Zoom Genie] Waiting for email input or profile/dashboard URL...')
                result = wait_for_element_or_url(driver, By.ID, EMAIL_INPUT_ID, expected_urls=["/profile", "/dashboard"], timeout=LOGIN_WAIT)
                if result == 'url':
                    log_info('[Zoom Genie] User already advanced to profile/dashboard. Skipping email entry.')
                    return True
                # --- Begin Human Mimic Integration ---
                from core import human_mimic
                # Find email input and mimic mouse movement and typing (clear only if not already correct)
                email_elem = wait_for_element(driver, By.ID, EMAIL_INPUT_ID, timeout=LOGIN_WAIT)
                current_email = email_elem.get_attribute('value')
                # Diagnostic: Screenshot, HTML, and log before email entry
                log_and_screenshot(driver, '[Zoom Genie] Before email entry', 'zoom_login_before_email')
                save_html(driver, 'zoom_login_before_email')
                if current_email != email:
                    driver.execute_script("arguments[0].value = ''", email_elem)
                    human_mimic.mimic_mouse_movement(driver, email_elem)
                    human_mimic.mimic_typing(email_elem, email)
                    log_info('[Zoom Genie] Email input mimicked.')
                else:
                    log_info('[Zoom Genie] Email already present, skipping re-entry.')
                # Diagnostic: Screenshot, HTML, and log after email entry
                log_and_screenshot(driver, '[Zoom Genie] After email entry', 'zoom_login_after_email')
                save_html(driver, 'zoom_login_after_email')

                # Find password input and mimic mouse movement and typing (clear only if not already correct)
                result = wait_for_element_or_url(driver, By.ID, PASSWORD_INPUT_ID, expected_urls=["/profile", "/dashboard"], timeout=LOGIN_WAIT)
                if result == 'url':
                    log_info('[Zoom Genie] User already advanced to profile/dashboard. Skipping password entry.')
                    return True
                password_elem = wait_for_element(driver, By.ID, PASSWORD_INPUT_ID, timeout=LOGIN_WAIT)
                current_password = password_elem.get_attribute('value')
                # Diagnostic: Screenshot, HTML, and log before password entry
                log_and_screenshot(driver, '[Zoom Genie] Before password entry', 'zoom_login_before_password')
                save_html(driver, 'zoom_login_before_password')
                if current_password != password:
                    driver.execute_script("arguments[0].value = ''", password_elem)
                    human_mimic.mimic_mouse_movement(driver, password_elem)
                    human_mimic.mimic_typing(password_elem, password)
                    log_info('[Zoom Genie] Password input mimicked.')
                else:
                    log_info('[Zoom Genie] Password already present, skipping re-entry.')
                # Diagnostic: Screenshot, HTML, and log after password entry
                log_and_screenshot(driver, '[Zoom Genie] After password entry', 'zoom_login_after_password')
                save_html(driver, 'zoom_login_after_password')

                # Mimic random page interaction before clicking Sign In
                human_mimic.mimic_page_interaction(driver)

                # === Improved: If email or password field is empty, fill it before clicking Sign In ===
                email_value = email_elem.get_attribute('value')
                password_value = password_elem.get_attribute('value')
                if not email_value:
                    driver.execute_script("arguments[0].value = ''", email_elem)
                    human_mimic.mimic_mouse_movement(driver, email_elem)
                    human_mimic.mimic_typing(email_elem, email)
                    log_info('[Zoom Genie] Autofilled empty email input before Sign In.')
                if not password_value:
                    driver.execute_script("arguments[0].value = ''", password_elem)
                    human_mimic.mimic_mouse_movement(driver, password_elem)
                    human_mimic.mimic_typing(password_elem, password)
                    log_info('[Zoom Genie] Autofilled empty password input before Sign In.')
                # Double-check after attempting to fill
                email_value = email_elem.get_attribute('value')
                password_value = password_elem.get_attribute('value')
                if not email_value or not password_value:
                    log_error('[Zoom Genie] Cannot proceed: Email or password field is still empty after autofill attempt.')
                    log_and_screenshot(driver, '[Zoom Genie] Still empty email or password before Sign In', 'zoom_login_empty_fields_error')
                    save_html(driver, 'zoom_login_empty_fields_error')
                    return False

                # Wait for and robustly click the Sign In button
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                def is_signin_clickable(driver):
                    btn = driver.find_element(By.ID, SIGN_IN_BTN_ID)
                    # Must be enabled, visible, not aria-disabled, and not covered
                    return (
                        btn.is_enabled() and btn.is_displayed() and btn.get_attribute('aria-disabled') != 'true' and btn.get_attribute('disabled') is None
                    )
                # Diagnostic: Screenshot, HTML, and log before clicking Sign In

                # === New: After clicking Sign In, check for OTP verification URL ===
                # (User must complete OTP manually if detected)
                def check_for_otp_verification(driver):
                    otp_url_prefix = "https://zoom.us/signin/otp/verify_help?"
                    current_url = driver.current_url
                    if current_url.startswith(otp_url_prefix):
                        log_warning('[Zoom Genie] OTP verification required. User intervention needed.')
                        log_and_screenshot(driver, '[Zoom Genie] OTP verification required', 'zoom_login_otp_required')
                        save_html(driver, 'zoom_login_otp_required')
                        print('\n[Zoom Genie] OTP verification page detected.')
                        print('Please complete the OTP verification in your browser window.')
                        input('When finished, press Enter here to continue...')
                        # Refresh the page after user completes OTP
                        driver.refresh()
                        # Wait for profile/dashboard or login success
                        return True
                    return False
                sign_in_btn = driver.find_element(By.ID, SIGN_IN_BTN_ID)
                btn_state = {
                    'enabled': sign_in_btn.is_enabled(),
                    'displayed': sign_in_btn.is_displayed(),
                    'aria-disabled': sign_in_btn.get_attribute('aria-disabled'),
                    'disabled': sign_in_btn.get_attribute('disabled'),
                    'class': sign_in_btn.get_attribute('class')
                }
                log_and_screenshot(driver, f"[Zoom Genie] Before clicking Sign In. Button state: {btn_state}", 'zoom_login_before_signin')
                save_html(driver, 'zoom_login_before_signin')
                try:
                    WebDriverWait(driver, 30).until(is_signin_clickable)
                    sign_in_btn = driver.find_element(By.ID, SIGN_IN_BTN_ID)
                    human_mimic.mimic_mouse_movement(driver, sign_in_btn)
                    human_mimic.random_pause(0.1, 0.8)
                    sign_in_btn.click()
                    log_info('[Zoom Genie] Sign In button mimicked and clicked.')
                except Exception as e:
                    # Enhanced diagnostics: capture exact reason for Sign In button not being clickable/enabled
                    btn_state = {
                        'enabled': sign_in_btn.is_enabled(),
                        'displayed': sign_in_btn.is_displayed(),
                        'aria-disabled': sign_in_btn.get_attribute('aria-disabled'),
                        'disabled': sign_in_btn.get_attribute('disabled'),
                        'class': sign_in_btn.get_attribute('class'),
                        'rect': driver.execute_script('return arguments[0].getBoundingClientRect();', sign_in_btn)
                    }
                    log_and_screenshot(driver, f"[Zoom Genie] Sign In button NOT clickable/enabled: {e}. Button state: {btn_state}", 'zoom_login_signin_not_clickable')
                    save_html(driver, 'zoom_login_signin_not_clickable')
                    log_error(f'[Zoom Genie] Sign In button not clickable/enabled after wait: {e}. Button state: {btn_state}')
                    # Try OCR on the screenshot to extract visible error messages
                    try:
                        from tools.extract_text_from_images import extract_text_from_image
                        ocr_text = extract_text_from_image('screenshots/zoom_login_signin_not_clickable.png')
                        if ocr_text.strip():
                            log_info(f'[Zoom Genie] OCR-detected error text after Sign In failure: {ocr_text.strip()}')
                    except Exception as ocr_e:
                        log_warning(f'[Zoom Genie] OCR extraction failed: {ocr_e}')
                    raise
                # Diagnostic: Screenshot, HTML, and log after clicking Sign In
                log_and_screenshot(driver, '[Zoom Genie] After clicking Sign In', 'zoom_login_after_signin')
                save_html(driver, 'zoom_login_after_signin')

                # Wait for login result with periodic URL check for slow networks
                log_and_screenshot(driver, '[Zoom Genie] Login submitted. Waiting for login result...', 'zoom_login_waiting_login_result')
                save_html(driver, 'zoom_login_waiting_login_result')
                log_info('[Zoom Genie] Login submitted. Waiting for login result (profile/dashboard or Sign In button re-enabled)...')
                start_time = time.time()
                import urllib.parse
                last_url = None
                while time.time() - start_time < LOGIN_RESULT_WAIT:
                    current_url = driver.current_url
                    parsed_url = urllib.parse.urlparse(current_url)
                    path = parsed_url.path.lower()
                    # Detect explicit page refresh (URL returns to login page after being elsewhere)
                    if last_url and last_url != current_url and path in ["/signin", "/login"]:
                        log_info(f'[Zoom Genie] Page refresh detected, resetting login attempt (URL: {current_url})')
                        break  # Exit polling loop to allow retry logic to handle the refresh
                    # Robust: Only count as success if path is exactly /profile or /dashboard (not substring)
                    if path in ["/profile", "/dashboard"]:
                        log_info(f'[Zoom Genie] Login successful: redirected to {path}.')
                        return True
                    # Detect common user intervention pages (e.g., 2FA, challenge, user intervention)
                    if any(x in path for x in ["/challenge", "/userintervention", "/verify", "/2fa", "/auth", "/mfa"]):
                        log_warning(f'[Zoom Genie] User intervention required: redirected to {path}.')
                        log_and_screenshot(driver, f'[Zoom Genie] User intervention required at {path}', 'zoom_login_user_intervention')
                        save_html(driver, 'zoom_login_user_intervention')
                        return False  # Or raise a special exception if desired
                    # Prevent infinite loop on repeated 'success' URL
                    if last_url == current_url:
                        time.sleep(1)
                    last_url = current_url
                    # Old code below used 'd', which caused NameError. Now use 'driver' directly (KISS/DRY):
                    # url = driver.current_url
                    # if '/profile' in url or '/dashboard' in url:
                    #     return 'profile'
                    # try:
                    #     btn = driver.find_element(By.ID, SIGN_IN_BTN_ID)
                    #     enabled = btn.is_enabled() and 'is-disabled' not in btn.get_attribute('class') and 'is-loading' not in btn.get_attribute('class') and btn.get_attribute('disabled') is None
                    #     if enabled:
                    #         return 'signin_enabled'
                    # except Exception:
                    #     pass
                    # return False
                    # The above block is now obsolete and unreachable due to the polling logic above.

                login_waited = 0
                max_wait = LOGIN_WAIT * 3
                while login_waited < max_wait:
                    try:
                        result = WebDriverWait(driver, LOGIN_WAIT).until(login_result_condition)
                    except Exception:
                        result = None
                    if result == 'profile':
                        log_info('[Zoom Genie] Login successful! Profile/dashboard page detected.')
                        return True
                    elif result == 'signin_enabled':
                        log_warning('[Zoom Genie] Login failed or needs retry: Sign In button re-enabled.')
                        attempt += 1
                        break
                    else:
                        log_info('[Zoom Genie] Login still processing, waiting longer...')
                        login_waited += LOGIN_WAIT
                        time.sleep(2)
                else:
                    log_and_screenshot(driver, '[Zoom Genie] Login timed out after extended wait. No dashboard/profile or error detected.', 'zoom_login_timeout')
                    attempt += 1
                    continue

                # After login submit, check for reCAPTCHA error message
                try:
                    error_div = wait_for_element(driver, By.CSS_SELECTOR, RECAPTCHA_ERROR_SELECTOR, timeout=10)
                    error_msg = error_div.text.strip()
                    log_and_screenshot(driver, f'[Zoom Genie] Login Error Detected: {error_msg}', 'zoom_login_recaptcha_error')
                    # If it's a reCAPTCHA error, refresh and reset attempts
                    from config import RECAPTCHA_ERROR_TEXT, NETWORK_ERROR_TEXT
                    if RECAPTCHA_ERROR_TEXT.lower() in error_msg.lower():
                        log_warning('[Zoom Genie] reCAPTCHA error detected. Refreshing and resetting batch attempt counter.')
                        driver.refresh()
                        time.sleep(2)
                        attempt = 0
                        continue
                    if NETWORK_ERROR_TEXT.lower() in error_msg.lower():
                        log_warning('[Zoom Genie] Network error detected. Refreshing and resetting batch attempt counter.')
                        driver.refresh()
                        time.sleep(5)  # Increased delay before retrying on network error for robustness
                        attempt = 0
                        continue
                    raise CaptchaDetectedException(f'Zoom Login Error: {error_msg}')
                except Exception as e:
                    log_and_screenshot(driver, f'[Zoom Genie] Error checking for reCAPTCHA message: {type(e).__name__} - {e}', 'zoom_login_recaptcha_check_error')
                    try:
                        err_text = str(e)
                        from config import NETWORK_ERROR_TEXT, RECAPTCHA_ERROR_TEXT
                        if NETWORK_ERROR_TEXT.lower() in err_text.lower():
                            log_warning('[Zoom Genie] Network error detected in exception. Refreshing and resetting batch attempt counter.')
                            driver.refresh()
                            time.sleep(2)
                            attempt = 0
                            continue
                        if RECAPTCHA_ERROR_TEXT.lower() in err_text.lower():
                            log_warning('[Zoom Genie] reCAPTCHA error detected in exception. Refreshing and resetting batch attempt counter.')
                            driver.refresh()
                            time.sleep(2)
                            attempt = 0
                            continue
                    except Exception:
                        pass
                    attempt += 1
                    continue

                log_and_screenshot(driver, "Login failed: Unknown error (no dashboard, no network/reCAPTCHA error message)", 'zoom_login_unknown_error')
                attempt += 1
                continue

            except Exception as e:
                log_and_screenshot(driver, f'[Zoom Genie] Unexpected error during login attempt: {type(e).__name__} - {e}', 'zoom_login_unexpected_error')
                attempt += 1
                continue
        return False

    driver.get(ZOOM_SIGNIN_URL)
    log_info('[Zoom Genie] Starting login batch 1 (normal attempts)...')
    batch1_success = attempt_login_batch(1)
    if batch1_success:
        return True
    log_warning('[Zoom Genie] First login batch failed. Refreshing page and trying again...')
    driver.refresh()
    time.sleep(2)
    log_info('[Zoom Genie] Starting login batch 2 (after refresh)...')
    batch2_success = attempt_login_batch(2)
    if batch2_success:
        return True
    log_and_screenshot(driver, '[Zoom Genie] Both login batches failed. Aborting login.', 'zoom_login_final_failure')
    raise Exception("Zoom login failed after 6 attempts (3 normal + 3 after refresh).")
