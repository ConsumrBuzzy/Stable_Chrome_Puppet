# Chrome Puppet

A robust and extensible Chrome browser automation tool built with Selenium and Python. This project provides a stable and maintainable way to automate Chrome/Chromium browsers with built-in error handling, configuration management, and BeautifulSoup integration.

## Features

- 🚀 Automatic ChromeDriver management
- ⚙️ Flexible configuration system
- 🛡️ Built-in error handling and recovery
- 🧩 Extensible architecture
- 🔍 BeautifulSoup integration for HTML parsing
- 📦 Easy installation and setup
- 💾 Configurable download directories
- 🖥️ Support for both headless and headed modes
- 🔄 Context manager support for resource cleanup

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/stable_chrome_puppet.git
   cd stable_chrome_puppet
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

```python
from chrome_puppet import ChromePuppet, ChromeConfig

# Create a custom configuration
config = ChromeConfig(
    headless=False,
    window_size=(1600, 900),
    download_dir="path/to/downloads"
)

# Use the browser
with ChromePuppet(config=config) as browser:
    # Navigate to a website
    browser.get("https://example.com")
    
    # Get page content as BeautifulSoup
    soup = browser.get_soup()
    print(soup.title.text)
```

## Configuration

The `ChromeConfig` class allows you to customize the browser behavior:

```python
config = ChromeConfig(
    headless=True,  # Run in headless mode
    window_size=(1920, 1080),  # Browser window size
    user_agent="Custom User Agent String",
    timeout=30,  # Default timeout in seconds
    chrome_type=ChromeType.GOOGLE,  # Or ChromeType.CHROMIUM
    download_dir="./downloads",  # Custom download directory
    chrome_arguments=[
        "--disable-notifications",
        "--disable-infobars"
    ]
)
```

## Examples

### Basic Usage

```python
from chrome_puppet import ChromePuppet

with ChromePuppet() as browser:
    browser.get("https://quotes.toscrape.com/")
    soup = browser.get_soup()
    quotes = soup.find_all('div', class_='quote')
    for quote in quotes:
        print(quote.find('span', class_='text').text)
```

### Handling Dynamic Content

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

with ChromePuppet() as browser:
    browser.get("https://example.com/dynamic")
    
    # Wait for an element to be present
    element = WebDriverWait(browser.driver, 10).until(
        EC.presence_of_element_located((By.ID, "dynamic-element"))
    )
    
    # Interact with the element
    element.click()
```

## Project Structure

```
stable_chrome_puppet/
├── __init__.py           # Package initialization
├── browser.py            # Main browser automation class
├── config.py             # Configuration classes
├── utils.py              # Utility functions
├── example.py            # Example usage
├── requirements.txt      # Project dependencies
└── README.md            # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
