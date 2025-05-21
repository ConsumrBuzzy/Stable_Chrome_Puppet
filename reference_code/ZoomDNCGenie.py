"""
ZoomDNCGenie.py
A CLI tool to add a 10-digit phone number to both Zoom Contact Center and Zoom Workplace DNC lists.

- Loads Zoom credentials from a .env file
- Uses Selenium for browser automation (visible, not headless)
- Always selects all relevant dropdowns for full DNC coverage
- Logs actions and prints results to the user

Implementation skeleton, ready for incremental development and testing.
"""

import os
import sys
import time
import logging
import platform
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from colorama import init as colorama_init, Fore, Style

# ========== Logging Setup ==========
timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"zoom_dnc_genie_log_{timestamp}.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ZoomDNCGenie.log', encoding='utf-8')
    ]
)

# ========== Python/Chrome Architecture Check ==========
def check_architecture():
    import struct
    py_arch = struct.calcsize("P") * 8
    chrome_arch = "64-bit" if platform.machine().endswith('64') else "32-bit"
    if (py_arch == 32 and chrome_arch == "64-bit") or (py_arch == 64 and chrome_arch == "32-bit"):
        print(Fore.YELLOW + f"[WARNING] Python is {py_arch}-bit but your Chrome is {chrome_arch}. This can cause driver errors. Consider matching architectures." + Style.RESET_ALL)
        logging.warning(f"Python is {py_arch}-bit but Chrome is {chrome_arch}. Potential driver mismatch.")

# ========== Load Credentials ==========
load_dotenv()
ZOOM_EMAIL = os.getenv("ZOOM_EMAIL")
ZOOM_PASSWORD = os.getenv("ZOOM_PASSWORD")

# ========== Early Environment Variable Check ==========
def check_env_vars():
    missing = []
    if not ZOOM_EMAIL:
        missing.append("ZOOM_EMAIL")
    if not ZOOM_PASSWORD:
        missing.append("ZOOM_PASSWORD")
    if missing:
        print(Fore.RED + f"Missing required environment variables: {', '.join(missing)}.\nPlease set them in your .env file." + Style.RESET_ALL)
        logging.error(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

# ========== Input Validation ==========
def get_phone_number():
    """Prompt user for a 10-digit phone number (no symbols)."""
    while True:
        phone = input("Enter a 10-digit phone number (numbers only): ").strip()
        if phone.isdigit() and len(phone) == 10:
            return phone
        print("Invalid input. Please enter exactly 10 digits (no spaces or symbols).")

# ========== Selenium Setup ==========
import struct
import urllib.request
import zipfile
import re
import subprocess

# ========== Chrome Version Detection ==========
def get_chrome_version():
    """Detect installed Chrome version via registry or command line."""
    version = None
    try:
        # Try registry (Windows)
        import winreg
        reg_path = r"SOFTWARE\\Google\\Chrome\\BLBeacon"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
        version, _ = winreg.QueryValueEx(key, "version")
        winreg.CloseKey(key)
    except Exception:
        # Try command line
        try:
            proc = subprocess.run([
                r"C:\Program Files\Google\Chrome\Application\chrome.exe", "--version"],
                capture_output=True, text=True)
            out = proc.stdout.strip() or proc.stderr.strip()
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)", out)
            if match:
                version = match.group(1)
        except Exception:
            pass
    return version

# ========== Chrome Bitness Detection ==========
def get_chrome_bitness():
    """Detect Chrome bitness by inspecting the executable."""
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        return None
    with open(chrome_path, 'rb') as f:
        header = f.read(0x1000)
        if b'PE\x00\x00L\x01\x00\x00' in header:
            return '32'
        elif b'PE\x00\x00d\x86\x00\x00' in header or b'PE\x00\x00\x64\x86\x00\x00' in header:
            return '64'
    # Fallback: use directory
    return '64' if 'Program Files' in chrome_path else '32'

# ========== Python Bitness Detection ==========
def get_python_bitness():
    return str(struct.calcsize("P") * 8)

# ========== Chromedriver Download ==========
def download_chromedriver(version, bitness, dest_path):
    """Download chromedriver.exe for given version and bitness to dest_path."""
    base_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win{bitness}/chromedriver-win{bitness}.zip"
    print(Fore.YELLOW + f"[INFO] Downloading chromedriver {version} ({bitness}-bit) from {base_url}" + Style.RESET_ALL)
    logging.info(f"Downloading chromedriver {version} ({bitness}-bit) from {base_url}")
    zip_path = dest_path + ".zip"
    try:
        urllib.request.urlretrieve(base_url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith('chromedriver.exe'):
                    zip_ref.extract(member, os.path.dirname(dest_path))
                    src = os.path.join(os.path.dirname(dest_path), member)
                    os.rename(src, dest_path)
        os.remove(zip_path)
        print(Fore.GREEN + f"[INFO] chromedriver.exe downloaded to {dest_path}" + Style.RESET_ALL)
        logging.info(f"chromedriver.exe downloaded to {dest_path}")
        return True
    except Exception as e:
        print(Fore.RED + f"[ERROR] Failed to download chromedriver: {e}" + Style.RESET_ALL)
        logging.error(f"Failed to download chromedriver: {e}")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        return False

# ========== Adaptive Driver Setup ==========
def create_driver():
    """Fully adaptive Chrome driver setup with bitness and version checks."""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_driver = os.path.join(script_dir, 'chromedriver.exe')

    # 1. Check for local chromedriver.exe
    if os.path.isfile(local_driver):
        print(Fore.YELLOW + "[INFO] Using local chromedriver.exe in script directory." + Style.RESET_ALL)
        logging.info("Using local chromedriver.exe in script directory.")
        service = Service(local_driver)
        try:
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except OSError as e:
            print(Fore.RED + f"[ERROR] Local chromedriver.exe failed to launch: {e}" + Style.RESET_ALL)
            logging.error(f"Local chromedriver.exe failed: {e}")
            # Remove and try next method
            os.remove(local_driver)

    # 2. Detect Chrome version and bitness
    chrome_version = get_chrome_version()
    chrome_bitness = get_chrome_bitness() or '64'
    python_bitness = get_python_bitness()
    print(Fore.CYAN + f"[INFO] Detected Chrome version: {chrome_version}, Chrome bitness: {chrome_bitness}-bit, Python bitness: {python_bitness}-bit" + Style.RESET_ALL)
    logging.info(f"Detected Chrome version: {chrome_version}, Chrome bitness: {chrome_bitness}-bit, Python bitness: {python_bitness}-bit")

    # 3. If bitness mismatch, warn and try to download matching chromedriver
    if chrome_version and chrome_bitness == python_bitness:
        # Download and use matching chromedriver
        if download_chromedriver(chrome_version, python_bitness, local_driver):
            service = Service(local_driver)
            try:
                driver = webdriver.Chrome(service=service, options=options)
                return driver
            except OSError as e:
                print(Fore.RED + f"[ERROR] Downloaded chromedriver.exe failed to launch: {e}" + Style.RESET_ALL)
                logging.error(f"Downloaded chromedriver.exe failed: {e}")
                os.remove(local_driver)
    elif chrome_bitness != python_bitness:
        print(Fore.RED + f"[ERROR] Bitness mismatch: Chrome is {chrome_bitness}-bit, Python is {python_bitness}-bit. This will cause failures. Please align both to 64-bit if possible." + Style.RESET_ALL)
        logging.error(f"Bitness mismatch: Chrome {chrome_bitness}-bit, Python {python_bitness}-bit")
        # Try to download anyway
        if chrome_version:
            if download_chromedriver(chrome_version, python_bitness, local_driver):
                service = Service(local_driver)
                try:
                    driver = webdriver.Chrome(service=service, options=options)
                    return driver
                except OSError as e:
                    print(Fore.RED + f"[ERROR] Downloaded chromedriver.exe failed to launch: {e}" + Style.RESET_ALL)
                    logging.error(f"Downloaded chromedriver.exe failed: {e}")
                    os.remove(local_driver)
        print(Fore.RED + "[FATAL] Could not resolve driver mismatch. Exiting." + Style.RESET_ALL)
        sys.exit(1)

    # 4. Fallback: webdriver_manager
    try:
        print(Fore.YELLOW + "[INFO] Falling back to webdriver_manager." + Style.RESET_ALL)
        logging.info("Falling back to webdriver_manager.")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except OSError as e:
        if getattr(e, 'winerror', None) == 193:
            print("[INFO] ChromeDriver binary invalid. Clearing webdriver_manager cache and retrying...")
            logging.warning("ChromeDriver binary invalid. Clearing webdriver_manager cache and retrying...")
            # Clear webdriver_manager cache
            wdm_cache = os.path.expanduser(r"~/.wdm") if platform.system() != "Windows" else os.path.expandvars(r"%USERPROFILE%\.wdm")
            shutil.rmtree(wdm_cache, ignore_errors=True)
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        else:
            print(Fore.RED + f"[FATAL] All driver setup methods failed: {e}" + Style.RESET_ALL)
            logging.error(f"All driver setup methods failed: {e}")
            sys.exit(1)

# ========== Zoom Login ==========
def zoom_login(driver):
    """Log in to Zoom.us using provided credentials (selectors from cci_web_ref/login_ref.htm)."""
    driver.get("https://www.zoom.us/signin")
    wait = WebDriverWait(driver, 20)
    try:
        # Use By.ID for email and password fields as per HTML reference
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_input.clear()
        email_input.send_keys(ZOOM_EMAIL)

        password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
        password_input.clear()
        password_input.send_keys(ZOOM_PASSWORD)

        # Use By.ID for the Sign In button (id="js_btn_login")
        sign_in_btn = wait.until(EC.element_to_be_clickable((By.ID, "js_btn_login")))
        sign_in_btn.click()

        # Wait for successful login (look for dashboard or profile icon)
        wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/profile')] | //div[contains(@class,'dashboard')]")))
        logging.info("Zoom login successful.")
        print("Logged in to Zoom.us successfully.")
    except Exception as e:
        logging.error(f"Zoom login failed: {e}")
        print(f"Zoom login failed: {e}")
        raise

# ========== Add to Zoom Contact Center DNC ==========
def add_to_contact_center_dnc(driver, phone_number):
    """Navigate and add phone number to Zoom Contact Center DNC (selectors from cci_web_ref)."""
    wait = WebDriverWait(driver, 20)
    try:
        # 1. Go to Contact Center Admin Preferences
        driver.get("https://zoom.us/cci/index/admin#/admin-preferences")
        time.sleep(3)  # Let the page load

        # 2. Click 'Block List' Tab (id='tab-blockList') with retry logic
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                block_tab = wait.until(EC.element_to_be_clickable((By.ID, "tab-blockList")))
                block_tab.click()
                logging.info(f"Clicked 'Block List' tab on attempt {attempt}.")
                time.sleep(2)
                break  # Success, exit retry loop
            except Exception as e:
                logging.warning(f"Attempt {attempt}: Could not click 'Block List' tab: {e}")
                # Take a screenshot for debugging
                screenshot_path = f"blocklist_tab_fail_attempt{attempt}.png"
                driver.save_screenshot(screenshot_path)
                logging.warning(f"Screenshot saved: {screenshot_path}")
                # Log current page URL and title
                logging.warning(f"Current URL: {driver.current_url}")
                logging.warning(f"Page Title: {driver.title}")
                # Print all visible tab names for debugging
                tabs = driver.find_elements(By.CSS_SELECTOR, ".zm-tabs__item.is-top")
                tab_texts = [t.text for t in tabs]
                print(f"[DEBUG] Visible tabs: {tab_texts}")
                logging.warning(f"[DEBUG] Visible tabs: {tab_texts}")
                if attempt < max_attempts:
                    time.sleep(2)  # Wait before next attempt
                else:
                    # After all retries, prompt manual intervention
                    input("All automatic attempts failed. Please manually click the 'Block List' tab in the browser, then press Enter to retry...")
                    try:
                        block_tab = wait.until(EC.element_to_be_clickable((By.ID, "tab-blockList")))
                        block_tab.click()
                        logging.info("Clicked 'Block List' tab after manual intervention.")
                        time.sleep(2)
                        break
                    except Exception as e2:
                        logging.error(f"Failed to click 'Block List' tab after manual intervention: {e2}")
                        raise

        # 3. Click 'Add' Button (use visible text)
        add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(),'Add')]]")))
        add_btn.click()
        time.sleep(1)

        # 4. Find 'Add a Block Rule' Dialog (role="dialog")
        popup = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog' and .//span[contains(text(),'Add a Block Rule')]]")))

        # 5. Match Type - open dropdown by role/button, select 'Phone Number Match'
        match_type_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(.,'Match Type')]/following-sibling::div//span[@role='button']")))
        match_type_dropdown.click()
        phone_match_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//dl[@role='listbox']//dd/div/span[contains(text(),'Phone Number Match')]")))
        phone_match_option.click()

        # 6. Enter phone number (aria-label='Phone Number', class='zm-input__inner')
        phone_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Phone Number' and contains(@class,'zm-input__inner')]")))
        phone_input.clear()
        phone_input.send_keys(phone_number)

        # 7. Channel Type - multi-select, click dropdown and select both
        channel_type_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(.,'Channel Type')]/following-sibling::div//div[contains(@class,'zm-multi-select-button')]")))
        channel_type_dropdown.click()
        for channel in ['SMS', 'Voice']:
            channel_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class,'zm-select-dropdown__item--content')]/span[contains(text(),'{channel}')]")))
            channel_option.click()
        # Click outside to close dropdown
        channel_type_dropdown.click()

        # 8. Block Type - multi-select, click dropdown and select both
        block_type_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(.,'Block Type')]/following-sibling::div//div[contains(@class,'zm-multi-select-button')]")))
        block_type_dropdown.click()
        for call_type in ['Inbound', 'Outbound']:
            block_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class,'zm-select-dropdown__item--content')]/span[contains(text(),'{call_type}')]")))
            block_option.click()
        block_type_dropdown.click()

        # 9. Click Save button (zm-button--primary, text 'Save')
        save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'zm-button--primary') and .//span[contains(text(),'Save')]]")))
        save_btn.click()

        # 10. Check for Success/Fail Message (zm-message__content)
        msg_elem = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "zm-message__content")))
        msg_text = msg_elem.text.strip()
        if 'Blocking rule is already implemented' in msg_text:
            logging.info(f"Contact Center: {phone_number} already in DNC. Message: {msg_text}")
            print(f"Contact Center: {phone_number} already in DNC. Message: {msg_text}")
        elif 'New rule added' in msg_text:
            logging.info(f"Contact Center: {phone_number} successfully added to DNC. Message: {msg_text}")
            print(f"Contact Center: {phone_number} successfully added to DNC. Message: {msg_text}")
        else:
            logging.warning(f"Contact Center: Unexpected message: {msg_text}")
            print(f"Contact Center: Unexpected message: {msg_text}")
    except Exception as e:
        logging.error(f"Contact Center DNC failed: {e}")
        print(f"Contact Center DNC failed: {e}")
        raise

# ========== Add to Zoom Workplace DNC ==========
def add_to_workplace_dnc(driver, phone_number):
    """Navigate and add phone number to Zoom Workplace DNC (selectors from cci_web_ref/workplace_ref.htm and workplace_dialog_ref.htm)."""
    wait = WebDriverWait(driver, 20)
    try:
        # 1. Go to Workplace Telephone page
        driver.get("https://zoom.us/pbx/page/telephone")
        time.sleep(3)  # Let the page load

        # 2. Click the 'Block List' tab if not already active
        try:
            block_list_tab = wait.until(EC.element_to_be_clickable((By.ID, "tab-companyBlockedList")))
            if "is-active" not in block_list_tab.get_attribute("class"):
                block_list_tab.click()
                time.sleep(1)
        except Exception:
            pass  # Already active or not needed

        # 3. Click 'Add' Button (zm-button--primary, text 'Add')
        add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'zm-button--primary') and .//span[contains(text(),'Add')]]")))
        add_btn.click()
        time.sleep(1)

        # 4. Find 'Add a Block Rule' Dialog (role="dialog")
        popup = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog' and .//span[contains(text(),'Add a Block Rule')]]")))

        # 5. Match Type - open dropdown by aria-label, select 'Phone Number Match'
        match_type_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@role='button' and contains(@aria-label, 'Match Type')]")))
        match_type_dropdown.click()
        phone_match_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//dl[@role='listbox']//dd/div/span[contains(text(),'Phone Number Match')]")))
        phone_match_option.click()

        # 6. Select US country code if not already set
        country_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Country/Region' and contains(@class,'zm-select-input__inner')]")))
        if not country_input.get_attribute('value').strip().endswith('+1'):
            country_input.click()
            us_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//dl[@role='listbox']//dd/div[contains(text(),'+1')]")))
            us_option.click()

        # 7. Enter phone number (aria-label='Phone Number', class='zm-input__inner')
        phone_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Phone Number' and contains(@class,'zm-input__inner')]")))
        phone_input.clear()
        phone_input.send_keys(phone_number)

        # 8. Block Type - multi-select, click dropdown and select both
        block_type_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(.,'Block Type')]/following-sibling::div//div[contains(@class,'zm-multi-select-button')]")))
        block_type_dropdown.click()
        for call_type in ['Inbound', 'Outbound']:
            block_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class,'zm-select-dropdown__item--content')]/span[contains(text(),'{call_type}')]")))
            block_option.click()
        block_type_dropdown.click()

        # 9. Click Save button (zm-button--primary, text 'Save')
        save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'zm-button--primary') and .//span[contains(text(),'Save')]]")))
        save_btn.click()

        # 10. Check for Success/Fail Message (zm-message__content)
        msg_elem = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "zm-message__content")))
        msg_text = msg_elem.text.strip()
        if 'Blocked number already exists' in msg_text:
            logging.info(f"Workplace: {phone_number} already in DNC. Message: {msg_text}")
            print(f"Workplace: {phone_number} already in DNC. Message: {msg_text}")
        elif 'Added Blocked Number Successfully' in msg_text:
            logging.info(f"Workplace: {phone_number} successfully added to DNC. Message: {msg_text}")
            print(f"Workplace: {phone_number} successfully added to DNC. Message: {msg_text}")
        else:
            logging.warning(f"Workplace: Unexpected message: {msg_text}")
            print(f"Workplace: Unexpected message: {msg_text}")
    except Exception as e:
        logging.error(f"Workplace DNC failed: {e}")
        print(f"Workplace DNC failed: {e}")
        raise

# ========== Main CLI Flow ==========
def check_env_vars():
    """Check if required environment variables are set."""
    required_vars = ['ZOOM_EMAIL', 'ZOOM_PASSWORD']
    for var in required_vars:
        if var not in os.environ:
            print(f"Error: Environment variable '{var}' is not set.")
            logging.error(f"Environment variable '{var}' is not set.")
            sys.exit(1)

def main():
    """Main CLI workflow for Zoom DNC Genie."""
    colorama_init(autoreset=True)
    print(Fore.CYAN + "\n=== Zoom DNC Genie ===\n" + Style.RESET_ALL)
    check_architecture()
    check_env_vars()
    phone_number = get_phone_number()

    driver = create_driver()
    try:
        zoom_login(driver)
        # Allow user to manually intervene for one-time codes or extra auth
        print(Fore.YELLOW + "\nIf you see a one-time code prompt, MFA, or need to complete any manual steps in the browser, do so now." + Style.RESET_ALL)
        input(Fore.YELLOW + "When finished, press Enter here to continue..." + Style.RESET_ALL)
        logging.info("Paused for user manual intervention after login (e.g., one-time code, MFA, or additional auth step).")

        # Define the URLs for each DNC process
        CONTACT_CENTER_DNC_URL = "https://admin.zoom.us/contactcenter/dnc"
        WORKPLACE_DNC_URL = "https://admin.zoom.us/workplace/dnc"

        # Re-navigate to Contact Center DNC page
        print(Fore.YELLOW + f"\nNavigating to Contact Center DNC page: {CONTACT_CENTER_DNC_URL}" + Style.RESET_ALL)
        driver.get(CONTACT_CENTER_DNC_URL)
        print(Fore.CYAN + f"[INFO] Now at: {driver.current_url}" + Style.RESET_ALL)
        print(Fore.CYAN + f"[INFO] Page title: {driver.title}" + Style.RESET_ALL)
        input(Fore.YELLOW + "Review the browser. When ready for Contact Center DNC automation, press Enter to continue..." + Style.RESET_ALL)

        try:
            add_to_contact_center_dnc(driver, phone_number)
        except Exception as e:
            # On failure, save screenshot and print page info
            screenshot_path = f"contact_center_dnc_error_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            print(Fore.RED + f"[ERROR] Contact Center DNC failed. Screenshot saved as {screenshot_path}" + Style.RESET_ALL)
            print(Fore.YELLOW + f"[DEBUG] Current page URL: {driver.current_url}" + Style.RESET_ALL)
            print(Fore.YELLOW + f"[DEBUG] Current page title: {driver.title}" + Style.RESET_ALL)
            logging.error(f"Contact Center DNC failed: {e}")
            logging.error(f"Screenshot saved as {screenshot_path}")
            logging.error(f"Page URL: {driver.current_url}")
            logging.error(f"Page title: {driver.title}")
            raise

        # Re-navigate to Workplace DNC page
        print(Fore.YELLOW + f"\nNavigating to Workplace DNC page: {WORKPLACE_DNC_URL}" + Style.RESET_ALL)
        driver.get(WORKPLACE_DNC_URL)
        print(Fore.CYAN + f"[INFO] Now at: {driver.current_url}" + Style.RESET_ALL)
        print(Fore.CYAN + f"[INFO] Page title: {driver.title}" + Style.RESET_ALL)
        input(Fore.YELLOW + "Review the browser. When ready for Workplace DNC automation, press Enter to continue..." + Style.RESET_ALL)

        try:
            add_to_workplace_dnc(driver, phone_number)
        except Exception as e:
            screenshot_path = f"workplace_dnc_error_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            print(Fore.RED + f"[ERROR] Workplace DNC failed. Screenshot saved as {screenshot_path}" + Style.RESET_ALL)
            print(Fore.YELLOW + f"[DEBUG] Current page URL: {driver.current_url}" + Style.RESET_ALL)
            print(Fore.YELLOW + f"[DEBUG] Current page title: {driver.title}" + Style.RESET_ALL)
            logging.error(f"Workplace DNC failed: {e}")
            logging.error(f"Screenshot saved as {screenshot_path}")
            logging.error(f"Page URL: {driver.current_url}")
            logging.error(f"Page title: {driver.title}")
            raise

        print(Fore.GREEN + f"Successfully processed {phone_number} in both DNC systems." + Style.RESET_ALL)
        logging.info(f"Completed DNC process for {phone_number}.")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nOperation cancelled by user (KeyboardInterrupt)." + Style.RESET_ALL)
        logging.warning("Operation cancelled by user (KeyboardInterrupt)")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(Fore.RED + f"Fatal error: {e}" + Style.RESET_ALL)
        sys.exit(1)
    finally:
        # Always close the browser, even on error
        try:
            driver.quit()
        except Exception as close_err:
            logging.warning(f"Error closing driver: {close_err}")

if __name__ == "__main__":
    main()
