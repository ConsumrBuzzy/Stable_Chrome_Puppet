# Chrome Puppet

A robust and extensible Chrome browser automation tool built with Selenium and Python. This project provides a stable and maintainable way to automate Chrome/Chromium browsers with built-in error handling, configuration management, and BeautifulSoup integration.

## Features

- 🚀 Self-contained Chrome and ChromeDriver management
- 🔄 Automatic browser version detection and compatibility handling
- 🧩 Extensible base class for different website platforms
- 🛡️ Built-in error handling and recovery
- 🖥️ Support for both headless and headed modes
- 🔍 Integration with BeautifulSoup for HTML parsing
- 🧹 Automatic resource cleanup
- ⏱️ Configurable wait strategies
- 📊 Comprehensive logging
- 📸 Screenshot capture with timestamps
- 💾 Configurable download directories
- 🔄 Context manager support for resource cleanup

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/consumrbuzzy/chrome-puppet.git
   cd chrome-puppet
   ```

2. **Set up a virtual environment (recommended)**
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   For development:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Quick Start

### Basic Usage

```python
from chrome_puppet import ChromePuppet

# Initialize Chrome Puppet (runs in headless mode by default)
with ChromePuppet() as browser:
    # Navigate to a website
    browser.get("https://www.example.com")
    
    # Get page title
    print(f"Page title: {browser.title}")
    
    # Take a screenshot (saved to screenshots/ directory)
    screenshot_path = browser.take_screenshot("example_page")
    print(f"Screenshot saved to: {screenshot_path}")
```

### Advanced Configuration

```python
from chrome_puppet import ChromePuppet, ChromeConfig

# Create a custom configuration
config = ChromeConfig(
    headless=False,  # Run in visible mode
    window_size=(1366, 768),
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    download_dir="path/to/downloads",
    implicit_wait=10,  # seconds
    verbose=True  # Enable debug logging
)

# Use the custom configuration
with ChromePuppet(config=config) as browser:
    browser.get("https://www.example.com")
    print(f"Current URL: {browser.driver.current_url}")
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
