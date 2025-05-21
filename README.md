# Chrome Puppet

> **Automate Chrome with confidence** - A robust, production-ready browser automation framework

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Chrome Puppet is a Python framework that makes browser automation simple and reliable. Built on top of Selenium, it provides a clean, intuitive API for automating Chrome/Chromium browsers with built-in best practices for stability and maintainability.

## ✨ Features

- **Modern API**: Intuitive Python interface for browser control
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Robust Error Handling**: Comprehensive error handling and recovery
- **Automatic ChromeDriver Management**: No need to manually manage ChromeDriver versions
- **Headless Mode**: Run browsers in headless mode for CI/CD pipelines
- **Extensible**: Easy to extend with custom functionality

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Chrome/Chromium browser

### Installation

```bash
# Install from PyPI
pip install chrome-puppet

# Or install from source
git clone https://github.com/consumrbuzzy/chrome-puppet.git
cd chrome-puppet
pip install -e .
```

### Basic Usage

```python
from chrome_puppet import ChromePuppet

# Create a browser instance and navigate to a page
with ChromePuppet() as browser:
    browser.get("https://example.com")
    print(f"Page title: {browser.title}")
```

For more detailed examples, see [EXAMPLES.md](EXAMPLES.md).

## 🛠 Project Structure

```text
chrome-puppet/
├── core/                    # Core browser automation code
│   ├── __init__.py
│   ├── browser/             # Browser implementation
│   │   ├── __init__.py
│   │   ├── base.py          # Base browser class
│   │   ├── chrome.py        # Chrome implementation
│   │   ├── element.py       # Element interactions
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── navigation.py    # Navigation utilities
│   │   └── screenshot.py    # Screenshot functionality
│   ├── config.py            # Configuration management
│   └── utils/               # Utility functions
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── base_test.py         # Base test class
│   ├── conftest.py          # Pytest configuration
│   ├── test_data/           # Test data files
│   └── test_browser.py      # Browser automation tests
├── examples/                # Example scripts
│   └── browser_example.py   # Example usage
├── .gitignore
├── CHANGELOG.md
├── EXAMPLES.md
├── LICENSE
├── pyproject.toml
├── README.md
├── requirements.txt         # Runtime dependencies
└── requirements-dev.txt     # Development dependencies
```

## 📚 Documentation

- [Examples](EXAMPLES.md) - Comprehensive examples and usage patterns
- [API Reference](docs/API.md) - Detailed API documentation (coming soon)
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute to the project

## 🧪 Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=core tests/
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/chrome-puppet.git
   cd chrome-puppet
   ```

2. **Set up a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   # source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

   For development:
   ```bash
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
├── chrome.py            # Main Chrome browser implementation
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
