"""
human_mimic.py
Utilities for simulating human-like behavior in Selenium automation to reduce bot detection risk (e.g., reCAPTCHA v3).
All functions follow PEP 8, DRY, KISS, and SOLID principles.
"""
import random
import time
from selenium.webdriver.common.action_chains import ActionChains


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

def mimic_mouse_movement(driver, element, steps=12):
    """Move mouse to the element in a human-like, non-linear path. Enhanced viewport check and logging."""
    from selenium.common.exceptions import MoveTargetOutOfBoundsException
    import logging
    try:
        # Enhanced: Try to center the element in the viewport
        if not is_element_in_viewport(driver, element):
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
        if not is_element_in_viewport(driver, element):
            # Log details for debugging
            rect = driver.execute_script("return arguments[0].getBoundingClientRect();", element)
            window_size = driver.get_window_size()
            logging.warning(
                f"[human_mimic] Element not fully in viewport after scroll. "
                f"rect: {rect}, window: {window_size}. Skipping mouse movement.")
            return
        location = element.location_once_scrolled_into_view
        size = element.size
        window_size = driver.get_window_size()
        actions = ActionChains(driver)
        # Start at a random point near the element, but clamp to window
        start_x = max(0, min(location['x'] + random.randint(-30, 30), window_size['width'] - 1))
        start_y = max(0, min(location['y'] + random.randint(-30, 30), window_size['height'] - 1))
        end_x = max(0, min(location['x'] + size['width'] // 2, window_size['width'] - 1))
        end_y = max(0, min(location['y'] + size['height'] // 2, window_size['height'] - 1))
        current_point = [start_x, start_y]
        driver.execute_script("window.scrollTo(arguments[0], arguments[1]);", start_x, start_y)
        for _ in range(steps):
            # Move towards the center in small, jittery steps, clamped to window
            jitter_x = random.randint(-5, 5)
            jitter_y = random.randint(-5, 5)
            next_x = max(0, min(current_point[0] + (end_x - current_point[0]) // (steps - _ + 1) + jitter_x, window_size['width'] - 1))
            next_y = max(0, min(current_point[1] + (end_y - current_point[1]) // (steps - _ + 1) + jitter_y, window_size['height'] - 1))
            move_x = next_x - current_point[0]
            move_y = next_y - current_point[1]
            actions.move_by_offset(move_x, move_y)
            current_point = [next_x, next_y]
            random_pause(0.02, 0.15)
        actions.move_to_element(element).perform()
        random_pause(0.1, 0.5)
    except MoveTargetOutOfBoundsException as e:
        logging.warning(f"[human_mimic] MoveTargetOutOfBoundsException: {e}. Skipping mouse movement for this element.")
    except Exception as e:
        logging.warning(f"[human_mimic] Unexpected exception in mimic_mouse_movement: {e}")


def mimic_typing(element, text, typo_chance=0.07, min_delay=0.07, max_delay=0.23):
    """Type text into an element with random pauses and occasional typos."""
    for char in text:
        # Randomly decide to make a typo
        if random.random() < typo_chance:
            typo = random.choice('abcdefghijklmnopqrstuvwxyz')
            element.send_keys(typo)
            random_pause(min_delay, max_delay)
            element.send_keys(Keys.BACKSPACE)
        element.send_keys(char)
        random_pause(min_delay, max_delay)


def mimic_typing(element, text, typo_chance=0.07, min_delay=0.07, max_delay=0.23):
    """Type text into an element with random delays and occasional typos/backspaces."""
    for char in text:
        if random.random() < typo_chance:
            # Simulate a typo and correction
            typo = random.choice('abcdefghijklmnopqrstuvwxyz')
            element.send_keys(typo)
            random_pause(0.04, 0.12)
            element.send_keys('\b')  # backspace
            random_pause(0.04, 0.12)
        element.send_keys(char)
        random_pause(min_delay, max_delay)


def random_scroll(driver, min_scroll=50, max_scroll=600):
    """Scroll the page by a random amount up or down."""
    scroll_amount = random.randint(min_scroll, max_scroll)
    if random.random() < 0.5:
        scroll_amount = -scroll_amount
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
    random_pause(0.2, 0.7)


from selenium.webdriver.common.by import By

def mimic_page_interaction(driver):
    """Randomly hover/click/scroll on non-essential elements to simulate human curiosity."""
    # Example: hover over random buttons or links
    elements = driver.find_elements(By.XPATH, '//a|//button')
    if elements:
        elem = random.choice(elements)
        try:
            ActionChains(driver).move_to_element(elem).perform()
            random_pause(0.1, 0.5)
        except Exception:
            pass
    # Random scroll
    random_scroll(driver)
    random_pause(0.1, 0.5)

# Additional utilities can be added as needed for tab switching, focus/blur, etc.
