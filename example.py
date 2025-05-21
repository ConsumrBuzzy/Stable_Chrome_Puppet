"""Example usage of ChromePuppet for web automation."""
import logging
from pathlib import Path

from chrome_puppet import ChromePuppet, ChromeConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Run the example script."""
    # Create a custom configuration
    config = ChromeConfig(
        headless=False,  # Set to True for headless mode
        window_size=(1600, 900),
        download_dir=str(Path.home() / "Downloads/chrome_puppet"),
        chrome_arguments=[
            "--disable-notifications",
            "--disable-infobars"
        ]
    )
    
    # Initialize the browser
    with ChromePuppet(config=config) as browser:
        try:
            # Navigate to a website
            browser.get("https://quotes.toscrape.com/js/")
            
            # Get the page as BeautifulSoup
            soup = browser.get_soup()
            
            if soup:
                # Extract quotes (these are loaded via JavaScript)
                quotes = soup.find_all('div', class_='quote')
                print(f"\nFound {len(quotes)} quotes:")
                
                for i, quote in enumerate(quotes[:5], 1):
                    text = quote.find('span', class_='text')
                    author = quote.find('small', class_='author')
                    
                    if text and author:
                        print(f"\n{i}. {text.get_text()}")
                        print(f"   — {author.get_text()}")
            
            # Example: Wait for user input before closing
            if not config.headless:
                input("\nPress Enter to close the browser...")
                
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            if not config.headless:
                input("Press Enter to close the browser after error...")

if __name__ == "__main__":
    main()
