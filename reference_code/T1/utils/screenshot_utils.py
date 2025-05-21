import os
import datetime
from utils.logging_utils import get_logger

# Always use the top-level /shots directory relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS_DIR = os.path.join(PROJECT_ROOT, 'shots')
os.makedirs(SHOTS_DIR, exist_ok=True)

def save_screenshot(driver, name_prefix="screenshot"):
    """
    Saves a screenshot to the shots directory with a timestamp and logs the path.
    Returns the screenshot path.
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name_prefix}_{ts}.png"
    path = os.path.join(SHOTS_DIR, filename)
    driver.save_screenshot(path)
    get_logger().info(f"Screenshot saved as {path}")
    return path
