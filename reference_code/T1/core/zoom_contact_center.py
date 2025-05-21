"""
zoom_contact_center.py
Handles all logic for adding a phone number to the Zoom Contact Center DNC list.
Uses element_finder utilities for robust web automation.
"""

# Import datetime for timestamping screenshots and logs
import datetime

from colorama import Fore, Style
import logging
from utils.selenium_utils import wait_for_element, wait_for_clickable, wait_and_fill, wait_and_click, log_and_screenshot
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from utils.logging_utils import log_info, log_warning, log_error
from config import DEFAULT_WAIT

from config import ZOOM_CONTACT_CENTER_ADMIN_URL

def add_to_contact_center_dnc(driver: object, phone_number: str) -> None:
    """
    Navigate and add phone number to Zoom Contact Center DNC (ported from ZoomDNCGenie.py).
    Uses robust waits, retries, and logging. See ZoomDNCGenie.py for original logic.
    """
    import time
    try:
        # Set up Selenium wait for robust element handling
        wait = WebDriverWait(driver, DEFAULT_WAIT)
        # 1. Go to Contact Center Admin Preferences
        log_info('[Contact Center] Navigating to Admin Preferences...')
        # Use the correct variable name for the Contact Center DNC URL
        # Use the centralized config value for the Contact Center Admin Preferences URL
        driver.get(ZOOM_CONTACT_CENTER_ADMIN_URL)
        time.sleep(3)  # Let the page load

        # 2. Click 'Block List' Tab
        print(Fore.CYAN + '[Contact Center] Looking for Block List Tab (id="tab-blockList")...' + Style.RESET_ALL)
        logging.info('[Contact Center] Looking for Block List Tab (id="tab-blockList")...')
        wait_and_click(driver, By.ID, "tab-blockList", timeout=DEFAULT_WAIT)
        logging.info('[Contact Center] Block List Tab found and clicked.')
        time.sleep(2)

        logging.info('[Contact Center] Looking for Add Rule Button (primary, text="Add new rule")...')
        try:
            wait_and_click(driver, By.XPATH, "//button[contains(@class,'zm-button--primary') and .//span[contains(text(),'Add new rule')]]", timeout=DEFAULT_WAIT)
            logging.info('[Contact Center] Add Rule Button found and clicked.')
            time.sleep(2)
        except (NoSuchElementException, ElementNotInteractableException) as e:
            # Gracefully handle Selenium element lookup/interact errors
            log_warning(f"[Contact Center] Could not find or click Add Rule Button: {type(e).__name__}: {e}")
            log_and_screenshot(driver, f'Add Rule Button not found. Exception: {type(e).__name__}, URL: {driver.current_url}', 'contact_center_add_rule_error')
            return
        except Exception as e:
            log_error(f"[Contact Center] Unexpected error clicking Add Rule Button: {type(e).__name__}: {e}")
            log_and_screenshot(driver, f'Unexpected error clicking Add Rule Button. Exception: {type(e).__name__}, URL: {driver.current_url}', 'contact_center_add_rule_unexpected')
            return

        # 4. Wait for the Add Block Rule dialog using a robust, targeted selector
        print(Fore.CYAN + '[Contact Center] Waiting for Add Block Rule dialog (optimized)...' + Style.RESET_ALL)
        logging.info('[Contact Center] Waiting for Add Block Rule dialog (optimized)...')
        timedate = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_name = f'contact_center_after_add_rule_click_{timedate}.png'
        driver.save_screenshot(screenshot_name)
        logging.info(f'Screenshot saved as {screenshot_name}')
        try:
            # Log the text and HTML of all visible dialog titles for debugging
            dialogs = driver.find_elements(By.XPATH, "//div[contains(@class,'zm-dialog__wrapper')]//div[@role='dialog']")
            for d in dialogs:
                if d.is_displayed():
                    try:
                        title_elem = d.find_element(By.XPATH, ".//span[contains(@class,'zm-dialog__title')]")
                        logging.info(f"[Contact Center] Visible dialog title text: '{title_elem.text}'")
                        logging.info(f"[Contact Center] Dialog title HTML: {title_elem.get_attribute('outerHTML')}")
                    except Exception as e:
                        logging.info(f"[Contact Center] No title found in dialog: {e}")

            # Wait for the Add Block Rule dialog to be visible using a robust, targeted XPath
            wait_dialog = WebDriverWait(driver, DEFAULT_WAIT * 2)
            dialog = wait_dialog.until(EC.visibility_of_element_located((
                By.XPATH,
                "//div[contains(@class,'zm-dialog__wrapper')]//div[@role='dialog' and .//span[@class='zm-dialog__title' and normalize-space(text())='Add a Block Rule']]"
            )))
            logging.info('[Contact Center] Dialog found. Proceeding to interact with dropdowns.')

            # --- NEW: Explicitly wait for Save button to be clickable ---
            try:
                save_btn = WebDriverWait(dialog, DEFAULT_WAIT).until(
                    lambda d: d.find_element(By.XPATH, ".//button[.//span[contains(text(),'Save')] and not(@disabled)]")
                )
                logging.info('[Contact Center] Save button found and enabled.')
            except Exception as save_wait_err:
                logging.error(f"[Contact Center] Save button not found or not enabled: {save_wait_err}")
                log_and_screenshot(driver, f'Save button not found after dialog appeared. Exception: {type(save_wait_err).__name__}, Message: {save_wait_err}', f'contact_center_save_btn_not_found_{timedate}')
                return
            # --- END NEW ---
            # Fixed: Removed duplicate and mis-indented block for logging dialog titles (previously caused IndentationError)
            # The Save button wait logic is now the last step before normal dialog interaction resumes.

            # Click the Match Type dropdown (robust: <span role='button'> selector)
            try:
                match_type_dropdown = WebDriverWait(dialog, DEFAULT_WAIT).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        ".//span[@role='button' and contains(@class, 'zm-select-span__inner')]"
                    ))
                )
                match_type_dropdown.click()
                logging.info('[Contact Center] Clicked Match Type dropdown.')
            except Exception as e:
                logging.error(f"[Contact Center] Could not interact with Match Type dropdown: {e}")
                # Dump dialog HTML for diagnostics
                try:
                    html_path = f'shots/contact_center_dialog_match_type_error_{timedate}.html'
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(dialog.get_attribute('outerHTML'))
                    logging.error(f"[Contact Center] Dialog HTML dumped to {html_path}")
                except Exception as html_err:
                    logging.error(f"[Contact Center] Could not save dialog HTML: {html_err}")
                log_and_screenshot(driver, f'Match Type dropdown interaction failed: {e}', f'contact_center_match_type_error_{timedate}')
                return

            # Wait for dropdown options to become visible, then select 'Phone Number Match' (robust: option text)
            try:
                dropdown_option = WebDriverWait(dialog, DEFAULT_WAIT).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        ".//dd[contains(@class,'zm-select-dropdown__item') and .//span[normalize-space(text())='Phone Number Match']]"
                    ))
                )
                dropdown_option.click()
                logging.info("[Contact Center] Selected 'Phone Number Match' from Match Type dropdown.")
            except Exception as e:
                logging.error(f"[Contact Center] Could not select 'Phone Number Match': {e}")
                # Dump dialog HTML for diagnostics
                try:
                    html_path = f'shots/contact_center_dropdown_option_error_{timedate}.html'
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(dialog.get_attribute('outerHTML'))
                    logging.error(f"[Contact Center] Dialog HTML dumped to {html_path}")
                except Exception as html_err:
                    logging.error(f"[Contact Center] Could not save dialog HTML: {html_err}")
                log_and_screenshot(driver, f"Dropdown option selection failed: {e}", f'contact_center_dropdown_option_error_{timedate}')
                return

            # NOTE: Selector rationale: Using <span role='button'> and dropdown <dd> by visible text for maximum resilience against class/id changes. See project documentation for details.

            # Enter the phone number (US-only, no need to change country code)
            # Robust: input field that is not the select input
            phone_input = dialog.find_element(
                By.XPATH,
                ".//div[contains(@class,'input-phone-number')]//input[@type='text' and not(contains(@class,'zm-select-input__inner'))]"
            )
            wait_and_fill(driver, By.XPATH, ".//div[contains(@class,'input-phone-number')]//input[@type='text' and not(contains(@class,'zm-select-input__inner'))]", phone_number, timeout=DEFAULT_WAIT)
            logging.info(f"[Contact Center] Entered phone number: {phone_number}")
            # Small step: added logging for phone number entry

            logging.info(f"[Contact Center] Entered phone number: {phone_number}")
        except Exception as e:
            logging.warning(f"[Contact Center] Could not complete dialog interaction: {e}")
            # Extra debugging: log all visible dialog titles
            try:
                dialogs = driver.find_elements(By.XPATH, "//div[contains(@class,'zm-dialog__wrapper')]//div[@role='dialog']")
                titles = [d.find_element(By.XPATH, ".//span[contains(@class,'zm-dialog__title')]").text for d in dialogs if d.is_displayed()]
                logging.warning(f"[Contact Center] Visible dialog titles at error: {titles}")
            except Exception as diag_err:
                logging.warning(f"[Contact Center] Could not enumerate dialog titles: {diag_err}")
            log_and_screenshot(driver, f'Error in dialog interaction: {type(e).__name__}, Message: {e}', f'contact_center_dialog_interaction_error_{timedate}')
            return

        # Step 4: Select both Inbound and Outbound in the multi-select dropdown
        try:
            # Find and open the multi-select dropdown (look for label or aria-label if possible)
            multi_select_btn = dialog.find_element(By.XPATH, ".//div[contains(@aria-label, 'multi select') or contains(@class, 'zm-multi-select') or .//label[contains(text(), 'Direction')]]//button | .//button[contains(@aria-label, 'multi select')]")
            multi_select_btn.click()
            time.sleep(0.5)
            # Find and check Inbound and Outbound checkboxes
            for direction in ['Inbound', 'Outbound']:
                try:
                    # Fixed XPath: closing parenthesis for the contains() function
                    checkbox = dialog.find_element(By.XPATH, f".//input[@type='checkbox' and (contains(@aria-label, '{direction}') or contains(@name, '{direction}'))]")
                    if not checkbox.is_selected():
                        checkbox.click()
                        logging.info(f"[Contact Center][DIAG] Checked '{direction}' direction.")
                    else:
                        logging.info(f"[Contact Center][DIAG] '{direction}' already checked.")
                except Exception as e:
                    logging.warning(f"[Contact Center][DIAG] Could not check '{direction}': {e}")
            # Click the Apply button in the multi-select dropdown
            try:
                apply_btn = dialog.find_element(By.XPATH, ".//button[.//span[contains(text(), 'Apply')]]")
                apply_btn.click()
                logging.info("[Contact Center][DIAG] Clicked 'Apply' on direction multi-select.")
            except Exception as e:
                logging.warning(f"[Contact Center][DIAG] Could not click 'Apply' in multi-select: {e}")
            time.sleep(0.5)
        except Exception as e:
            logging.warning(f"[Contact Center][DIAG] Multi-select direction logic failed: {e}")

        # Step 5: Voice/SMS multi-select: select all (Filter (All))
        try:
            # Try to find and open the Voice/SMS multi-select dropdown (look for label, aria-label, or placeholder)
            voice_sms_btn = dialog.find_element(By.XPATH, ".//div[contains(@aria-label, 'multi select') or contains(@class, 'zm-multi-select')][not(.//label[contains(text(), 'Direction')])]//button | .//button[contains(@aria-label, 'multi select') and not(ancestor::div[.//label[contains(text(), 'Direction')]])]")
            voice_sms_btn.click()
            time.sleep(0.5)
            # Find the 'Filter (All)' checkbox and select it if not already checked
            filter_all_checkbox = dialog.find_element(By.XPATH, ".//input[@type='checkbox' and (@aria-label='Filter (All)' or @value='Filter (All)')]" )
            if not filter_all_checkbox.is_selected():
                filter_all_checkbox.click()
                logging.info("[Contact Center][DIAG] Checked 'Filter (All)' for Voice/SMS multi-select.")
            else:
                logging.info("[Contact Center][DIAG] 'Filter (All)' already checked for Voice/SMS multi-select.")
            # Click the Apply button in the multi-select dropdown
            try:
                apply_btn = dialog.find_element(By.XPATH, ".//button[.//span[contains(text(), 'Apply')]]")
                apply_btn.click()
                logging.info("[Contact Center][DIAG] Clicked 'Apply' on Voice/SMS multi-select.")
            except Exception as e:
                logging.warning(f"[Contact Center][DIAG] Could not click 'Apply' in Voice/SMS multi-select: {e}")
            time.sleep(0.5)
        except Exception as e:
            logging.warning(f"[Contact Center][DIAG] Voice/SMS multi-select select-all logic failed: {e}")

        # Step 6: Click the Save/Confirm button
        try:
            save_btn = dialog.find_element(By.XPATH, ".//button[contains(@class, 'zm-button--primary') and (contains(., 'Save') or contains(., 'Confirm'))]")
            save_btn.click()
            logging.info("[Contact Center][DIAG] Clicked Save/Confirm button.")
        except Exception as e:
            logging.warning(f"[Contact Center][DIAG] Could not click Save/Confirm: {e}")

        # [Legacy dialog diagnostic code removed: superseded by new robust dialog detection and interaction logic.]
            logging.error('[Contact Center] Dialog not found or not visible. Listing all zm-dialog and zm-dialog__title elements for diagnostics...')
            dialogs = driver.find_elements(By.XPATH, "//div[contains(@class, 'zm-dialog')]")
            for idx, dlg in enumerate(dialogs):
                try:
                    title_elem = dlg.find_element(By.XPATH, ".//span[contains(@class, 'zm-dialog__title')]")
                    title = title_elem.text
                    title_visible = title_elem.is_displayed()
                except Exception:
                    title = '(no zm-dialog__title)'
                    title_visible = False
                print(f"[Contact Center][DIAG] Dialog {idx}: title='{title}' visible={dlg.is_displayed()} title_visible={title_visible}")
                logging.info(f"[Contact Center][DIAG] Dialog {idx}: title='{title}' visible={dlg.is_displayed()} title_visible={title_visible}")
            driver.save_screenshot('contact_center_dialog_not_found.png')
            logging.error('Screenshot saved as contact_center_dialog_not_found.png')
            raise

        # 5. Set Match Type to 'Prefix Match'
        print(Fore.CYAN + '[Contact Center] Setting Match Type to "Prefix Match"...' + Style.RESET_ALL)
        logging.info('[Contact Center] Setting Match Type to "Prefix Match"...')
        match_type_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@class,'zm-select-span__inner') and starts-with(@aria-label, 'Match Type')]")))
        match_type_dropdown.click()
        prefix_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@class,'zm-select-dropdown__item') and text()='Prefix Match']")))
        prefix_option.click()
        print(Fore.GREEN + '[Contact Center] Match Type set to Prefix Match.' + Style.RESET_ALL)
        logging.info('[Contact Center] Match Type set to Prefix Match.')

        # 6. Ensure Block Type is 'Inbound' (tag)
        print(Fore.CYAN + '[Contact Center] Ensuring Block Type is "Inbound"...' + Style.RESET_ALL)
        logging.info('[Contact Center] Ensuring Block Type is "Inbound"...')
        block_type_tag = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'tag-list')]//span[contains(@class,'zm-group-select__tags-text') and text()='Inbound']")))
        print(Fore.GREEN + '[Contact Center] Block Type is Inbound.' + Style.RESET_ALL)
        logging.info('[Contact Center] Block Type is Inbound.')

        # 7. Ensure Channel Type is 'SMS' (tag)
        print(Fore.CYAN + '[Contact Center] Ensuring Channel Type is "SMS"...' + Style.RESET_ALL)
        logging.info('[Contact Center] Ensuring Channel Type is "SMS"...')
        channel_type_tag = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'zm-form-item__content')]//span[contains(@class,'zm-group-select__tags-text') and text()='SMS']")))
        print(Fore.GREEN + '[Contact Center] Channel Type is SMS.' + Style.RESET_ALL)
        logging.info('[Contact Center] Channel Type is SMS.')

        # 8. Fill Phone Number Input
        print(Fore.CYAN + '[Contact Center] Entering phone number...' + Style.RESET_ALL)
        logging.info('[Contact Center] Entering phone number...')
        phone_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@class,'zm-input__inner') and @aria-label='Phone Number']")))
        phone_input.clear()
        phone_input.send_keys(phone_number)
        print(Fore.GREEN + '[Contact Center] Phone number entered.' + Style.RESET_ALL)
        logging.info('[Contact Center] Phone number entered.')

        # 9. Click Save Button
        print(Fore.CYAN + '[Contact Center] Clicking Save button...' + Style.RESET_ALL)
        logging.info('[Contact Center] Clicking Save button...')
        save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'zm-button--primary')]//span[contains(text(),'Save')]")))
        save_btn.click()
        print(Fore.GREEN + '[Contact Center] Save button clicked.' + Style.RESET_ALL)
        logging.info('[Contact Center] Save button clicked.')

        logging.info('[Contact Center] Match Type set.')

        # 6. Set Country/Region to United States
        print(Fore.CYAN + '[Contact Center] Setting Country/Region to United States...' + Style.RESET_ALL)
        logging.info('[Contact Center] Setting Country/Region to United States...')
        country_input = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "zm-select-input__inner")))
        country_input.click()
        country_input.clear()
        country_input.send_keys("United States")
        # Optionally select from dropdown if needed
        print(Fore.GREEN + '[Contact Center] Country/Region set.' + Style.RESET_ALL)
        logging.info('[Contact Center] Country/Region set.')

        # 7. Enter phone number
        print(Fore.CYAN + f'[Contact Center] Entering phone number: {phone_number}...' + Style.RESET_ALL)
        logging.info(f'[Contact Center] Entering phone number: {phone_number}...')
        phone_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Enter phone number']")))
        phone_input.clear()
        phone_input.send_keys(phone_number)
        print(Fore.GREEN + '[Contact Center] Phone number entered.' + Style.RESET_ALL)
        logging.info('[Contact Center] Phone number entered.')

        # 8. Wait for Block List Table
        print(Fore.CYAN + '[Contact Center] Waiting for Block List Table (id="block-list-table")...' + Style.RESET_ALL)
        logging.info('[Contact Center] Waiting for Block List Table (id="block-list-table")...')
        try:
            block_table = wait.until(EC.presence_of_element_located((By.ID, "block-list-table")))
            print(Fore.GREEN + '[Contact Center] Block List Table found.' + Style.RESET_ALL)
            logging.info('[Contact Center] Block List Table found.')
        except Exception as e:
            print(Fore.RED + f'[Contact Center] Timeout: Block List Table not found. Exception: {type(e).__name__}, URL: {driver.current_url}' + Style.RESET_ALL)
            logging.error(f'Timeout: Block List Table not found. Exception: {type(e).__name__}, URL: {driver.current_url}')
            driver.save_screenshot('block_list_table_error.png')
            logging.error('Screenshot saved as block_list_table_error.png')
            raise

        # 6. Select Block Type
        print(Fore.CYAN + '[Contact Center] Selecting Block Type: Inbound, Outbound...' + Style.RESET_ALL)
        logging.info('[Contact Center] Selecting Block Type: Inbound, Outbound...')
        block_type_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "block-type-dropdown")))
        block_type_dropdown.click()
        for call_type in ['Inbound', 'Outbound']:
            option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//span[contains(text(),'{call_type}')]")))
            option.click()
            print(Fore.GREEN + f'[Contact Center] Block Type selected: {call_type}' + Style.RESET_ALL)
            logging.info(f'[Contact Center] Block Type selected: {call_type}')
        block_type_dropdown.click()  # Close dropdown

        # 7. Click Save
        print(Fore.CYAN + '[Contact Center] Clicking Save button...' + Style.RESET_ALL)
        logging.info('[Contact Center] Clicking Save button...')
        save_btn = wait.until(EC.element_to_be_clickable((By.ID, "save-block-btn")))
        save_btn.click()
        print(Fore.GREEN + '[Contact Center] Save button clicked.' + Style.RESET_ALL)
        logging.info('[Contact Center] Save button clicked.')

        # 8. Wait for Success Toast
        print(Fore.CYAN + '[Contact Center] Waiting for success toast...' + Style.RESET_ALL)
        logging.info('[Contact Center] Waiting for success toast...')
        try:
            toast = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "zm-toast-success")))
            msg = toast.text
            print(Fore.GREEN + f'[Contact Center] Success: {msg}' + Style.RESET_ALL)
            logging.info(f'[Contact Center] Success: {msg}')
        except Exception as e:
            print(Fore.RED + f'[Contact Center] No confirmation detected after Save. Exception: {type(e).__name__}, URL: {driver.current_url}' + Style.RESET_ALL)
            logging.error(f'No confirmation detected after Save. Exception: {type(e).__name__}, URL: {driver.current_url}')
            driver.save_screenshot('contact_center_save_error.png')
            logging.error('Screenshot saved as contact_center_save_error.png')
            raise


        # 2. Click 'Block List' Tab (id='tab-blockList') with retry logic
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                block_tab = wait.until(EC.element_to_be_clickable((By.ID, "tab-blockList")))
                block_tab.click()
                break
            except Exception as e:
                if attempt == max_attempts:
                    logging.error(f"Could not click Block List tab: {e}")
                    raise
                time.sleep(1)

        # 3. Click 'Add' button (id='btn-add-block')
        add_btn = wait.until(EC.element_to_be_clickable((By.ID, "btn-add-block")))
        add_btn.click()

        # 4. Enter phone number (id='blockNumber')
        phone_input = wait.until(EC.presence_of_element_located((By.ID, "blockNumber")))
        phone_input.clear()
        phone_input.send_keys(phone_number)

        # 5. Select all campaigns (multi-select)
        campaign_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(.,'Campaign')]/following-sibling::div//div[contains(@class,'zm-multi-select-button')]")))
        campaign_dropdown.click()
        all_campaigns = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class,'zm-select-dropdown__item--content')]/span")))
        for campaign in all_campaigns:
            campaign.click()
        campaign_dropdown.click()  # Close dropdown

        # 6. Select all channels (multi-select)
        channel_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(.,'Channel')]/following-sibling::div//div[contains(@class,'zm-multi-select-button')]")))
        channel_dropdown.click()
        all_channels = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class,'zm-select-dropdown__item--content')]/span")))
        for channel in all_channels:
            channel.click()
        channel_dropdown.click()  # Close dropdown

        # 7. Set block reason (id='blockReason')
        reason_input = wait.until(EC.presence_of_element_located((By.ID, "blockReason")))
        reason_input.clear()
        reason_input.send_keys("Compliance")

        # 8. Block Type - multi-select, click dropdown and select both
        block_type_dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(.,'Block Type')]/following-sibling::div//div[contains(@class,'zm-multi-select-button')]")))
        block_type_dropdown.click()
        for call_type in ['Inbound', 'Outbound']:
            block_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//div[contains(@class,'zm-select-dropdown__item--content')]/span[contains(text(),'{call_type}')]")))
            block_option.click()
        block_type_dropdown.click()

        # 9. Click 'Save' (id='btn-save-block')
        save_btn = wait.until(EC.element_to_be_clickable((By.ID, "btn-save-block")))
        save_btn.click()

        # 10. Confirm success (look for toast or confirmation)
        toast = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "zm-toast-success")))
        msg = toast.text
        logging.info(f"Contact Center: {phone_number} successfully added to DNC. Message: {msg}")
        print(f"Contact Center: {phone_number} successfully added to DNC. Message: {msg}")
    except Exception as e:
        logging.error(f"Contact Center DNC failed: {e}")
        print(f"Contact Center DNC failed: {e}")
        raise

