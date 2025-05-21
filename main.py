from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

class ChromeWebDriverBase:
    """
    A base class for a Selenium Chrome WebDriver.
    Handles browser initialization, navigation, and page source retrieval for BS4.
    """
    def __init__(self, headless=True, user_agent=None):
        """
        Initializes the ChromeWebDriverBase.

        Args:
            headless (bool): Whether to run Chrome in headless mode. Defaults to True.
            user_agent (str, optional): Custom user agent string. Defaults to None.
        """
        self.driver = None
        self.headless = headless
        self.user_agent = user_agent
        self._initialize_driver()

    def _initialize_driver(self):
        """
        Sets up and initializes the Chrome WebDriver instance.
        """
        chrome_options = ChromeOptions()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")  # Recommended for headless
        chrome_options.add_argument("--window-size=1920,1080") # Standard window size
        chrome_options.add_argument("--log-level=3") # Suppress unnecessary console logs
        chrome_options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
        chrome_options.add_argument("--no-sandbox") # Bypass OS security model, USE WITH CAUTION

        if self.user_agent:
            chrome_options.add_argument(f"user-agent={self.user_agent}")
        else:
            # A generic user agent
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")

        # Automatically download and manage ChromeDriver
        service = ChromeService(ChromeDriverManager().install())

        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            # Optional: Set a default implicit wait (seconds)
            # self.driver.implicitly_wait(5)
            print("WebDriver initialized successfully.")
        except Exception as e:
            print(f"Error initializing WebDriver: {e}")
            raise  # Re-raise the exception to halt execution if driver fails

    def get_page_source(self, url, wait_time=5):
        """
        Navigates to a URL and returns the page source after a specified wait time.

        Args:
            url (str): The URL to navigate to.
            wait_time (int): Time in seconds to wait for dynamic content to load.
                             Consider using explicit waits for more robust solutions.

        Returns:
            str: The page source HTML, or None if an error occurs.
        """
        if not self.driver:
            print("WebDriver not initialized.")
            return None
        try:
            self.driver.get(url)
            print(f"Navigated to: {url}")
            # Simple wait for dynamic content. For complex pages, use Selenium's explicit waits.
            time.sleep(wait_time)
            return self.driver.page_source
        except Exception as e:
            print(f"Error navigating to {url} or getting page source: {e}")
            return None

    def get_soup(self, url, wait_time=5):
        """
        Navigates to a URL, gets the page source, and returns a BeautifulSoup object.

        Args:
            url (str): The URL to navigate to.
            wait_time (int): Time in seconds to wait for dynamic content.

        Returns:
            BeautifulSoup: A BeautifulSoup object for parsing, or None if an error occurs.
        """
        page_source = self.get_page_source(url, wait_time)
        if page_source:
            return BeautifulSoup(page_source, 'html.parser')
        return None

    def close_driver(self):
        """
        Closes the WebDriver.
        """
        if self.driver:
            try:
                self.driver.quit()
                print("WebDriver closed.")
            except Exception as e:
                print(f"Error closing WebDriver: {e}")
        self.driver = None # Ensure driver attribute is reset

# --- Example Usage ---
if __name__ == "__main__":
    # URL for testing (a site designed for scraping)
    test_url = "https://quotes.toscrape.com/js/" # This site uses JavaScript to load quotes

    # Initialize the browser (headless by default)
    # To run with a visible browser, set headless=False
    browser_base = None
    try:
        browser_base = ChromeWebDriverBase(headless=True)
        # browser_base = ChromeWebDriverBase(headless=False) # To see the browser in action

        if browser_base.driver: # Check if driver initialized successfully
            # Get BeautifulSoup object directly
            soup = browser_base.get_soup(test_url, wait_time=5)

            if soup:
                print(f"\nSuccessfully retrieved and parsed content from: {test_url}")
                # Example: Extract all quotes (these are in <span class="text"> elements)
                quotes = soup.find_all('span', class_='text')
                if quotes:
                    print(f"\nFound {len(quotes)} quotes:")
                    for i, quote in enumerate(quotes):
                        print(f"{i+1}. {quote.get_text(strip=True)}")
                else:
                    print("No quotes found with the specified selector.")

                # Example: Extract all author names
                authors = soup.find_all('small', class_='author')
                if authors:
                    print(f"\nFound {len(authors)} authors:")
                    for author in authors:
                        print(f"- {author.get_text(strip=True)}")
                else:
                    print("No authors found.")
            else:
                print(f"Could not retrieve soup object from {test_url}")
        else:
            print("Browser base could not be initialized. Exiting.")

    except Exception as e:
        print(f"An error occurred during the main execution: {e}")
    finally:
        if browser_base:
            browser_base.close_driver()