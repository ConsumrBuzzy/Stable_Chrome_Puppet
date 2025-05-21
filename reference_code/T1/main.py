"""
main.py
Entry point for the Zoom DNC Genie system.

Implements the top-level CLI, credential loading, logging, browser automation,
login, and DNC actions for both Zoom Contact Center and Zoom Workplace.
This script is modular and ready for future extension.

# Ported and refactored from ZoomDNCGenie.py (see Legacy directory for original).
# All main workflow, input validation, and error handling logic is derived from the monolithic version for full parity and robustness.
"""

# All imports must be at the top per PEP8 and to avoid UnboundLocalError/NameError
import os
import sys
import time
import subprocess  # For running diagnostics analyzer (PEP8)
from datetime import datetime, timezone
from utils.logging_utils import log_info, log_warning, log_error
import logging
from config import ZOOM_SIGNIN_URL, ZOOM_PROFILE_URL, ZOOM_DASHBOARD_URL, DEFAULT_WAIT, MAX_LOGIN_RETRIES
from utils.exceptions import ZoomLoginFailedException
from utils.selenium_utils import wait_for_element, wait_for_clickable, safe_click
from cli import prompt_phone_number
from dotenv import load_dotenv
from utils.env_utils import load_credentials  # Modular credential loader
from utils.browser_utils import create_driver  # Modular browser setup
from colorama import init as colorama_init, Fore, Style
from core.zoom_contact_center import add_to_contact_center_dnc  # Modular Contact Center logic
from core.zoom_workplace import add_to_workplace_dnc  # Modular Workplace logic
from core.zoom_login import zoom_login  # Modularized login with robust retry

# ========== Logging Setup ==========
def setup_logging():
    """
    Setup logging to ./logs directory. Creates ./logs if it doesn't exist.
    Each run is logged to a timestamped file in ./logs.
    """
    # os is already imported at the top per PEP8
    if not os.path.exists("logs"):
        os.makedirs("logs")
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join("logs", f"zoom_dnc_genie_log_{timestamp}.txt")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_filename, encoding='utf-8')
        ]
    )

def log_run_time(event: str):
    """Log a run start or end time event to shots/run_times.log in ISO format."""
    try:
        log_path = os.path.join(os.path.dirname(__file__), 'shots', 'run_times.log')
        with open(log_path, 'a', encoding='utf-8') as f:
            now = datetime.now(timezone.utc).isoformat()
            f.write(f"{event}: {now}\n")
    except Exception as e:
        print(f"[Zoom Genie] Failed to log run time: {e}")

# ========== Load Credentials ==========

# ========== Input Validation ==========
def get_phone_number():
    """Prompt user for a 10-digit phone number (no symbols). Ported from ZoomDNCGenie.py."""
    while True:
        phone = input("Enter a 10-digit phone number (numbers only): ").strip()
        if phone.isdigit() and len(phone) == 10:
            return phone
        log_error("Invalid input. Please enter exactly 10 digits (no spaces or symbols).")

# ========== Selenium WebDriver Setup ==========

# ========== Zoom Login ==========
# Removed old login logic, using modularized zoom_login module for robust retry on network errors

# ========== Main CLI Workflow ==========
def main():
    """Main CLI workflow for Zoom DNC Genie. Ported and refactored from ZoomDNCGenie.py."""
    colorama_init(autoreset=True)
    setup_logging()
    log_info("\n=== Zoom DNC Genie ===\n")
    log_info("=== Zoom DNC Genie Started ===")

    try:
        log_info("Prompting user for phone number input...")
        phone_number = get_phone_number()

        # Load credentials
        log_info("Loading credentials from .env...")
        email, password = load_credentials()

        # Create browser driver (stealth mode if USE_UC env var is set or --stealth CLI arg is present)
        log_info("Creating browser driver...")
        use_uc = os.getenv("USE_UC", "0").lower() in ("1", "true", "yes") or "--stealth" in sys.argv
        driver = create_driver(use_uc=use_uc)
        if use_uc:
            log_info("[main] Stealth mode enabled: using undetected-chromedriver (uc).")
        else:
            log_info("[main] Standard ChromeDriver mode.")

        # Login to Zoom
        log_info("Logging in to Zoom...")
        login_success = zoom_login(driver, email, password)
        if not login_success:
            log_error("Zoom login failed after retries. Exiting.")
            return

        # Manual intervention notice
        print(Fore.YELLOW + "\nIf you see a one-time code prompt, MFA, or need to complete any manual steps in the browser, do so now." + Style.RESET_ALL)
        logging.info("Prompting user for manual intervention after login.")
        input("When finished, press Enter here to continue...")
        logging.info("Paused for user manual intervention after login.")

        # Contact Center DNC
        print(Fore.CYAN + "Adding to Contact Center DNC..." + Style.RESET_ALL)
        logging.info("Adding to Contact Center DNC...")
        add_to_contact_center_dnc(driver, phone_number)

        # Workplace DNC
        print(Fore.CYAN + "Adding to Workplace DNC..." + Style.RESET_ALL)
        logging.info("Adding to Workplace DNC...")
        add_to_workplace_dnc(driver, phone_number)

        print(Fore.GREEN + "\n=== Zoom DNC Genie Complete ===\n" + Style.RESET_ALL)
        logging.info("=== Zoom DNC Genie Complete ===")

    except Exception as e:
        log_error(f"Fatal error: {e}")
        raise
    # Use only top-level imports in finally block to avoid UnboundLocalError (PEP8)
    finally:
        try:
            driver.quit()
        except Exception as close_err:
            logging.warning(f"Error closing driver: {close_err}")
        # Log run end time
        log_run_time('end')
        # Always run diagnostics analyzer at shutdown (normal or interrupted)
        analyzer_path = os.path.join(os.path.dirname(__file__), 'tools', 'analyze_diagnostics.py')
        if os.path.isfile(analyzer_path):
            print("\n[Zoom Genie] Running diagnostics analyzer...")
            try:
                subprocess.run([sys.executable, analyzer_path], check=True)
            except Exception as e:
                print(f"[Zoom Genie] Diagnostics analyzer failed: {e}")
        else:
            print(f"[Zoom Genie] Analyzer script not found: {analyzer_path}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        import logging
        logging.warning("[SYSTEM] Received CTRL+C (KeyboardInterrupt). Shutting down gracefully...")
        print("Shutdown complete.")
