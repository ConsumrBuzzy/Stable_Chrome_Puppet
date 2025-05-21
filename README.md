# Chrome Puppet

> **Automate Chrome with confidence** - A robust, production-ready browser automation framework

Chrome Puppet is a Python framework that makes browser automation simple and reliable. Built on top of Selenium, it provides a clean, intuitive API for automating Chrome/Chromium browsers with built-in best practices for stability and maintainability.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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

1. **Clone and set up the project**
   ```bash
   git clone https://github.com/consumrbuzzy/chrome-puppet.git
   cd chrome-puppet
   ```

2. **Set up a virtual environment**
   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   
   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the example**
   ```bash
   python examples/basic_usage.py
   ```

## 📚 Documentation

Explore our comprehensive documentation:

- [AGENT.md](AGENT.md) - Technical reference for developers and AI agents
- [API Reference](docs/API.md) - Detailed API documentation
- [Examples](examples/) - Practical code samples
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

### Basic Usage

```python
from core.browser.chrome import ChromeBrowser
from core.config import ChromeConfig
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure browser
config = ChromeConfig(
    headless=False,  # Set to True for headless mode
    window_size=(1200, 800),
    chrome_arguments=[
        "--disable-notifications",
        "--disable-extensions"
    ]
)

# Initialize browser
browser = None
try:
    print("Starting Chrome browser...")
    browser = ChromeBrowser(config)
    browser.start()
    
    # Navigate to a website
    print("Navigating to Google...")
    browser.navigate_to("https://www.google.com")
    
    # Get current URL
    print(f"Current URL: {browser.get_current_url()}")
    
    # Get page source (first 200 chars)
    print(f"Page source preview: {browser.get_page_source()[:200]}...")
    
    # Take a screenshot
    if browser.take_screenshot("screenshot.png"):
        print("Screenshot saved!")
        
except Exception as e:
    print(f"An error occurred: {e}")
    
finally:
    # Ensure browser is properly closed
    if browser:
        print("Stopping browser...")
        browser.stop()
```
    
    # Take a screenshot
    browser.screenshot.take_screenshot("example.png")
    
    # Find and interact with elements
    search_box = browser.element.find_element("css", "input[type='search']")
    browser.element.send_keys("Hello, World!", element=search_box)
    
    # Get page content
    content = browser.get_page_source()
    print(f"Page title: {browser.get_title()}")
```

## 🏗️ Project Structure

```
chrome-puppet/
├── core/                    # Core functionality
│   ├── browser/            # Browser automation code
│   │   ├── __init__.py
│   │   ├── chrome.py        # Chrome browser implementation
│   │   └── puppet.py       # High-level browser control
│   └── config.py           # Configuration management
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_basic.py       # Basic functionality tests
│   └── test_browser.py     # Browser-specific tests
├── examples/               # Example scripts
│   ├── browser_example.py  # Basic browser usage
│   └── simple_chrome.py    # Minimal example
├── .gitignore
├── LICENSE
├── README.md
└── requirements*.txt       # Dependencies
```

## Basic Usage

```python
from chrome_puppet import ChromePuppet, ChromeConfig

# Create a browser instance
config = ChromeConfig(
    headless=True,
    window_size=(1366, 768),
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."
)

with ChromePuppet(config=config) as browser:
    # Navigate to a page
    browser.get("https://example.com")
    
    # Get page title
    print(f"Page title: {browser.driver.title}")
    
    # Take a screenshot
    browser.save_screenshot("screenshot.png")
```

## Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# Run a specific test file
pytest tests/test_browser.py -v
```

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🧪 Running Tests

To run the test suite, follow these steps:

1. Install the development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run the tests:
   ```bash
   # Run all tests
   pytest -v
   
   # Run only browser tests
   pytest -m browser
   
   # Run tests with coverage report
   pytest --cov=core --cov-report=term-missing
   ```

3. For debugging tests, you can run Chrome in headful mode:
   ```bash
   pytest --headful
   ```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Run the test suite to ensure all tests pass
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Workflow

1. Create a virtual environment and activate it
2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   pre-commit install
   ```
3. Make your changes
4. Run tests and linters:
   ```bash
   black .
   flake8
   mypy .
   pytest
   ```
5. Update documentation if needed
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📬 Support

For support, please open an issue on our [GitHub Issues](https://github.com/consumrbuzzy/chrome-puppet/issues) page.

## 🔗 Related Projects

- [Selenium](https://www.selenium.dev/) - Web browser automation
- [Playwright](https://playwright.dev/) - Modern browser automation
- [Puppeteer](https://pptr.dev/) - Node.js browser automation

## 📊 Stats

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)

---

<div align="center">
  Made with ❤️ by the Chrome Puppet Team
</div>

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
