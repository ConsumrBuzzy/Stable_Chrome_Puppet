"""
Human-like interaction utilities for Selenium to reduce bot detection.
Inspired by legacy T1 implementation with improvements.
"""
import random
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import MoveTargetOutOfBoundsException
import logging

def random_pause(min_sec=0.3, max_sec=1.2):
    """Sleep for a random interval between min_sec and max_sec seconds."""
    time.sleep(random.uniform(min_sec, max_sec))

def is_element_in_viewport(driver, element):
    """Return True if the element is fully within the viewport, False otherwise."""
    return driver.execute_script(
        "var rect = arguments[0].getBoundingClientRect();"
        "return (rect.top >= 0 && rect.left >= 0 && "
        "rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) && "
        "rect.right <= (window.innerWidth || document.documentElement.clientWidth));",
        element)

def is_point_in_viewport(driver, x, y):
    """Check if a point (x,y) is within the current viewport."""
    try:
        viewport_width = driver.execute_script("return window.innerWidth || document.documentElement.clientWidth;")
        viewport_height = driver.execute_script("return window.innerHeight || document.documentElement.clientHeight;")
        scroll_x = driver.execute_script("return window.pageXOffset || document.documentElement.scrollLeft;")
        scroll_y = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop;")
        
        # Adjust for current scroll position
        abs_x = x + scroll_x
        abs_y = y + scroll_y
        
        return (0 <= abs_x <= viewport_width and 
                0 <= abs_y <= viewport_height)
    except:
        return False

def safe_move_to(driver, x, y, steps=8):
    """Safely move mouse to coordinates within viewport bounds."""
    try:
        # Get viewport dimensions
        viewport_width = driver.execute_script("return window.innerWidth || document.documentElement.clientWidth;")
        viewport_height = driver.execute_script("return window.innerHeight || document.documentElement.clientHeight;")
        
        # Ensure target is within viewport bounds
        x = max(0, min(x, viewport_width - 1))
        y = max(0, min(y, viewport_height - 1))
        
        # Get current mouse position
        try:
            current_x = driver.execute_script("return window.mouseX || 0;")
            current_y = driver.execute_script("return window.mouseY || 0;")
        except:
            current_x, current_y = 0, 0
        
        # Create a curved path to the target
        actions = ActionChains(driver)
        
        for i in range(1, steps + 1):
            progress = i / steps
            # Ease-in-out curve
            t = 0.5 - 0.5 * math.cos(progress * math.pi)
            
            # Calculate next point
            next_x = current_x + (x - current_x) * t
            next_y = current_y + (y - current_y) * t
            
            # Add some randomness
            if i < steps:
                next_x += random.uniform(-10, 10)
                next_y += random.uniform(-5, 5)
            
            # Ensure within bounds
            next_x = max(0, min(next_x, viewport_width - 1))
            next_y = max(0, min(next_y, viewport_height - 1))
            
            # Move to next point
            actions.move_by_offset(next_x - current_x, next_y - current_y)
            current_x, current_y = next_x, current_y
            
            # Small delay between movements
            random_pause(0.02, 0.05)
        
        actions.perform()
        return True
    except Exception as e:
        logging.warning(f"[human_mimic] Error in safe_move_to: {str(e)}")
        return False

def mimic_mouse_movement(driver, element, steps=12):
    """
    Move mouse to the element in a human-like, non-linear path.
    
    Args:
        driver: Selenium WebDriver instance
        element: WebElement to move to
        steps: Number of steps for the movement (more steps = smoother movement)
    """
    try:
        # First ensure element is in viewport
        if not is_element_in_viewport(driver, element):
            scroll_into_view(driver, element)
            random_pause(0.5, 1.0)  # Allow time for scrolling
        
        # Get element position
        location = element.location
        size = element.size
        
        # Calculate target point (center of element)
        target_x = location['x'] + (size['width'] // 2)
        target_y = location['y'] + (size['height'] // 2)
        
        # Move to the target
        if not safe_move_to(driver, target_x, target_y, steps):
            # Fallback to direct movement if safe_move fails
            try:
                ActionChains(driver).move_to_element(element).perform()
            except Exception as e:
                logging.warning(f"[human_mimic] Fallback move_to_element failed: {str(e)}")
        
        # Final small pause
        random_pause(0.1, 0.3)
        
    except Exception as e:
        logging.warning(f"[human_mimic] Error in mouse movement: {str(e)}")
        # Final fallback - try clicking without moving
        try:
            element.click()
        except:
            pass

def mimic_typing(element, text, typo_chance=0.07, min_delay=0.07, max_delay=0.23):
    """Type text into an element with random delays and occasional typos/backspaces."""
    for char in text:
        if random.random() < typo_chance:
            # Simulate a typo and correction
            typo = random.choice('abcdefghijklmnopqrstuvwxyz')
            element.send_keys(typo)
            random_pause(0.04, 0.12)
            element.send_keys(Keys.BACKSPACE)
            random_pause(0.04, 0.12)
        element.send_keys(char)
        random_pause(min_delay, max_delay)

def scroll_into_view(driver, element, block='center'):
    """
    Scroll an element into view with smooth behavior.
    
    Args:
        driver: Selenium WebDriver instance
        element: WebElement to scroll to
        block: Vertical alignment ('start', 'center', 'end', or 'nearest')
    """
    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: arguments[1], inline: 'nearest'});",
            element, block
        )
        random_pause(0.3, 0.8)  # Small delay after scrolling
        return True
    except Exception as e:
        logging.warning(f"[human_mimic] Error scrolling to element: {str(e)}")
        try:
            # Fallback to standard scrolling if smooth scrolling fails
            driver.execute_script("arguments[0].scrollIntoView();", element)
            return True
        except:
            return False

def mimic_page_interaction(driver):
    """Perform random human-like interactions with the page."""
    try:
        # Get viewport dimensions
        viewport_width = driver.execute_script("return window.innerWidth || document.documentElement.clientWidth;")
        viewport_height = driver.execute_script("return window.innerHeight || document.documentElement.clientHeight;")
        
        # Randomly scroll (50% chance)
        if random.random() < 0.5:
            try:
                # Scroll by a random amount (10-40% of viewport height)
                scroll_amt = random.randint(
                    int(viewport_height * 0.1), 
                    int(viewport_height * 0.4)
                )
                # Randomly scroll up or down
                if random.random() < 0.5:
                    scroll_amt = -scroll_amt
                
                driver.execute_script(f"window.scrollBy(0, {scroll_amt});")
                random_pause(0.5, 1.5)
            except Exception as e:
                logging.warning(f"[human_mimic] Error during scroll: {str(e)}")
        
        # Random mouse movement (60% chance)
        if random.random() < 0.6:
            try:
                # Generate random position within viewport
                target_x = random.randint(0, max(1, viewport_width - 1))
                target_y = random.randint(0, max(1, viewport_height - 1))
                
                # Move to the random position
                if not safe_move_to(driver, target_x, target_y, steps=random.randint(3, 8)):
                    # If safe_move fails, try a small relative move
                    try:
                        actions = ActionChains(driver)
                        actions.move_by_offset(
                            random.randint(-50, 50),
                            random.randint(-30, 30)
                        ).perform()
                    except:
                        pass
                
                random_pause(0.2, 0.5)
                
            except Exception as e:
                logging.warning(f"[human_mimic] Error in random mouse move: {str(e)}")
        
    except Exception as e:
        logging.warning(f"[human_mimic] Error in page interaction: {str(e)}")
        # Continue execution even if interaction fails
