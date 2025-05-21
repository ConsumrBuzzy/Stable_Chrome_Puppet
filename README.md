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

## System Requirements

- Python 3.8 or higher
- Chrome/Chromium browser installed
- Git (for development)

## Installation

### Quick Start (Windows)

1. **Clone the repository**

   ```powershell
   git clone https://github.com/consumrbuzzy/chrome-puppet.git
   cd chrome-puppet
   ```

2. **Run the setup script**

   ```powershell
   .\setup_env.ps1
   ```

   For development with additional tools:

   ```powershell
   .\setup_env.ps1 -Dev
   ```

### Manual Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/consumrbuzzy/chrome-puppet.git
   cd chrome-puppet
   ```

2. **Set up a virtual environment**

   **Windows:**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS/Linux:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   For development:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Project Structure

```
chrome-puppet/
├── .github/                 # GitHub workflows and issue templates
├── core/                    # Core browser automation code
│   ├── __init__.py
│   ├── browser.py          # Main browser automation class
│   ├── config.py           # Configuration management
│   └── orchestrator.py     # High-level browser orchestration
├── examples/               # Example scripts
├── screenshots/            # Directory for saved screenshots
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── base_test.py        # Base test class
│   ├── test_basic.py       # Basic functionality tests
│   ├── test_browser_init.py # Browser initialization tests
│   └── test_navigation.py  # Navigation tests
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── utils.py            # Helper utilities
├── .env.example           # Example environment variables
├── .gitignore
├── CHANGELOG.md           # Project changelog
├── LICENSE
├── main.py                # Command-line interface
├── pyproject.toml         # Project metadata and build configuration
├── README.md              # This file
├── requirements-dev.txt    # Development dependencies
├── requirements.txt       # Runtime dependencies
└── setup.py               # Package installation script
```

## Virtual Environment Setup

### Windows

```powershell
# Create virtual environment
python -m venv .venv

# Activate the virtual environment
.\\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### macOS/Linux

```bash
# Create virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### Using the Virtual Environment

- To activate the virtual environment, run the appropriate command above
- Your command prompt should show `(.venv)` at the beginning when activated
- To deactivate, simply type `deactivate`
- Always activate the virtual environment before running the project

## Environment Variables

Create a `.env` file in the project root based on `.env.example`:

```env
# Chrome settings
CHROME_HEADLESS=false
CHROME_WINDOW_SIZE=1920,1080
CHROME_IMPLICIT_WAIT=10

# Logging
LOG_LEVEL=INFO
LOG_FILE=chrome_puppet.log

# Browser settings
CHROME_PATH=auto  # Set to 'auto' for auto-detection or specify path
CHROME_VERSION_OVERRIDE=  # Leave empty for auto-detection
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
