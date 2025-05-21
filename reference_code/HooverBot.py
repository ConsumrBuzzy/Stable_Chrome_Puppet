import time
import json
from datetime import date, datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from dotenv import load_dotenv
import sqlite3
import logging
import sys

# ************* Configure Logging *************
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"dnc_bot_log_{timestamp}.txt"
logging.basicConfig(filename=log_filename, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
# **********************************************

# Load environment variables from .env file (if you have any)
load_dotenv()

# Telesero Credentials
password = "R0b0t!c47#"  # Replace with your actual password

# Server and Campaign Information
servers = [
    {"username": "I11\\TOBOR", "campaign_value": "710"},
    {"username": "I10\\TOBOR", "campaign_value": "990"},
    {"username": "IB9\\TOBOR", "campaign_value": "220"},
    {"username": "IB8\\TOBOR", "campaign_value": "750"},
    {"username": "IBL\\TOBOR", "campaign_value": "6400"}
]

# Web Driver Setup (Headless Mode)
options = webdriver.ChromeOptions()
#options.add_argument("--headless=new")
options.add_argument(
    r"--binary-location=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
)  # Update Chrome path if needed

# ChromeDriver setup using webdriver_manager (no manual download needed)
service = Service(ChromeDriverManager().install()) 

def add_to_blacklist(driver, phone_number):
    """Adds the phone number to the Blacklist."""
    try:
        driver.get("https://portal.teleserosuite.com/contact-center/blacklist/new")
        driver.implicitly_wait(5)  # Add implicit wait

        # Correct selector for phone number input
        phone_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "vicidial_filter_phone_number_type_fullPhoneNumber"))
        )
        phone_input.send_keys(phone_number)

        # Correct selector for submit button
        save_button = WebDriverWait(driver, 5).until(  
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Add to Blacklist']"))
        )
        save_button.click()
        logging.info(f"Added {phone_number} to Blacklist.")

    except Exception as e:
        logging.error(f"Error adding to Blacklist: {e}")

def add_to_dnc(driver, phone_number):
    """Adds the phone number to all DNC campaigns."""
    try:
        driver.get("https://portal.teleserosuite.com/contact-center/dnc/text")

        # Wait for the campaign dropdown to load and get all options
        campaign_dropdown = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "vicidial_dnc_text_type_campaignId"))
        )
        campaign_options = campaign_dropdown.find_elements(By.TAG_NAME, "option")
        campaign_values = [option.get_attribute("value") for option in campaign_options]

        # Iterate through each campaign value
        for campaign_value in campaign_values:
            for attempt in range(3):  # Retry loop for stale element
                try:
                    # Reload the DNC page for each campaign
                    driver.get("https://portal.teleserosuite.com/contact-center/dnc/text")

                    # Select the campaign by value
                    campaign_dropdown = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "vicidial_dnc_text_type_campaignId"))
                    )
                    campaign_dropdown.find_element(By.XPATH, f"//option[@value='{campaign_value}']").click()
                    time.sleep(5)  

                    # Re-locate elements after campaign selection
                    phone_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "vicidial_dnc_text_type_numbers"))
                    )
                    phone_input.clear()
                    phone_input.send_keys(phone_number)

                    submit_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[text()='Send Request']"))
                    )
                    submit_button.click()

                    logging.info(f"Added {phone_number} to DNC campaign: {campaign_value}")

                    # Wait for 15 seconds after submission
                    time.sleep(5) 

                    break  # Exit retry loop if successful

                except StaleElementReferenceException:
                    logging.warning(f"Stale element encountered. Retrying (attempt {attempt + 1})...")
                    time.sleep(15)  # Wait a bit before retrying

            if attempt == 2:  # Max retries reached
                logging.error(f"Max retries reached for DNC campaign: {campaign_value}. Skipping.")

    except Exception as e:
        logging.error(f"Error adding to DNC: {e}")



def run_dnc_bot(phone_number):
    """Main function to run the DNC bot."""
    for server_info in servers:
        username = server_info["username"]
        campaign_value = server_info["campaign_value"]

        try:
            driver = webdriver.Chrome(service=service, options=options)
            driver.implicitly_wait(5)

            logging.info(f"Attempting login for user: {username}, Campaign: {campaign_value}")

            # Login to Telesero
            driver.get("https://portal.teleserosuite.com/contact-center/monitoring/")
            driver.find_element(By.ID, "username").send_keys(username)
            driver.find_element(By.ID, "password").send_keys(password)
            driver.find_element(By.XPATH, "//button[@type='submit']").click()
            time.sleep(5)
            logging.info("Login successful")

            add_to_blacklist(driver, phone_number)
            add_to_dnc(driver, phone_number)

        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            screenshot_filename = f"error_screenshot_{timestamp}.png"
            if "driver" in locals():
                driver.save_screenshot(screenshot_filename)
            logging.error(
                f"Error occurred for user: {username}, Campaign: {campaign_value}. Error: {e}. Screenshot saved as {screenshot_filename}"
            )
        finally:
            if "driver" in locals():
                driver.quit()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        phone_number = sys.argv[1]
    else:
        phone_number = input("Enter the phone number to add: ")
    run_dnc_bot(phone_number)
