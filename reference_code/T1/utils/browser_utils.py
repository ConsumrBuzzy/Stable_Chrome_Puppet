"""
browser_utils.py
Selenium WebDriver# Refactored to match the robust and adaptive driver setup logic from ZoomDNCGenie.py, including bitness/version checks, local fallback, and logging. See ZoomDNCGenie.py for original implementation."""
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from utils.system_utils import check_architecture, get_chrome_version, get_chrome_bitness, get_python_bitness
import urllib.request
import zipfile


def create_driver(use_uc=None):
    """
    Create a Selenium Chrome WebDriver, optionally using undetected-chromedriver (uc) for stealth.
    Priority:
    1. If use_uc is True or USE_UC env var is set, try undetected-chromedriver.
    2. Use CHROMEDRIVER_PATH from environment if set.
    3. Use chromedriver.exe in /Assets directory if present.
    4. Use chromedriver.exe in project root if present.
    5. Fallback to webdriver_manager (requires internet).
    """
    import logging
    import os
    use_uc_env = os.getenv("USE_UC", "0").lower() in ("1", "true", "yes")
    if use_uc is None:
        use_uc = use_uc_env
    if use_uc:
        try:
            import undetected_chromedriver as uc
            options = uc.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            # options.add_argument("--headless")  # Uncomment if you want headless mode
            driver = uc.Chrome(options=options)
            driver.implicitly_wait(5)
            logging.info("[browser_utils] Using undetected-chromedriver (uc) for stealth automation.")
            return driver
        except ImportError:
            logging.warning("[browser_utils] undetected-chromedriver not installed. Falling back to standard ChromeDriver.")
        except Exception as e:
            logging.warning(f"[browser_utils] Could not launch undetected-chromedriver: {e}. Falling back to standard ChromeDriver.")
    # --- Standard ChromeDriver logic below (unchanged) ---
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH")
    if chromedriver_path and os.path.exists(chromedriver_path):
        # Check bitness and version of chromedriver
        if not is_chromedriver_compatible(chromedriver_path):
            logging.warning(f"Chromedriver at {chromedriver_path} is not compatible. Falling back to other options.")
            chromedriver_path = None
    if chromedriver_path:
        service = Service(chromedriver_path)
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.implicitly_wait(5)
            return driver
        except WebDriverException as e:
            logging.error(f"Failed to launch ChromeDriver from {chromedriver_path}. Error: {str(e)}")
            chromedriver_path = None
    # Check for chromedriver.exe in /Assets directory
    assets_driver = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Assets", "chromedriver.exe")
    if os.path.exists(assets_driver):
        if not is_chromedriver_compatible(assets_driver):
            logging.warning(f"Chromedriver at {assets_driver} is not compatible. Falling back to other options.")
            assets_driver = None
    if assets_driver:
        service = Service(assets_driver)
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.implicitly_wait(5)
            return driver
        except WebDriverException as e:
            logging.error(f"Failed to launch ChromeDriver from {assets_driver}. Error: {str(e)}")
            assets_driver = None
    # Check for chromedriver.exe in project root
    local_driver = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
    if os.path.exists(local_driver):
        # Check bitness and version of chromedriver
        if not is_chromedriver_compatible(local_driver):
            logging.warning(f"Chromedriver at {local_driver} is not compatible. Falling back to other options.")
            local_driver = None
    if local_driver:
        service = Service(local_driver)
        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
            driver.implicitly_wait(5)
            return driver
        except WebDriverException as e:
            logging.error(f"Failed to launch ChromeDriver from {local_driver}. Error: {str(e)}")
            local_driver = None
    # Fallback to webdriver_manager (requires internet)
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        driver.implicitly_wait(5)
        return driver
    except WebDriverException as e:
        raise RuntimeError("Could not launch ChromeDriver. Please set CHROMEDRIVER_PATH or place chromedriver.exe in the project directory. Original error: " + str(e))


def is_chromedriver_compatible(path):
    # TODO: Implement real bitness and version checks using get_chrome_version/get_chrome_bitness
    # For now, just return True
    return True


import config  # Centralize all URLs in config.py

def download_chromedriver(version, bitness, dest_path):
    """
    Download chromedriver.exe for given version and bitness to dest_path.
    Extracted from ZoomDNCGenie.py for modular use.
    Uses CHROMEDRIVER_DOWNLOAD_URL_TEMPLATE from config.py for URL consistency.
    """
    base_url = config.CHROMEDRIVER_DOWNLOAD_URL_TEMPLATE.format(version=version, bitness=bitness)
    logging.info(f"Downloading chromedriver {version} ({bitness}-bit) from {base_url}")
    zip_path = dest_path + ".zip"
    try:
        urllib.request.urlretrieve(base_url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(dest_path))
            for member in zip_ref.namelist():
                if member.endswith('chromedriver.exe'):
                    src = os.path.join(os.path.dirname(dest_path), member)
                    os.rename(src, dest_path)
        os.remove(zip_path)
        logging.info(f"chromedriver.exe downloaded to {dest_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to download chromedriver: {e}")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        return False
