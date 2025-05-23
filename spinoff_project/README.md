# Stable Chrome Puppet (Spinoff)

A lightweight, focused version of the Stable Chrome Puppet browser automation tool.

## Features

- Simple browser automation using Selenium WebDriver
- Configurable Chrome options
- Context manager support for safe resource cleanup
- Type hints for better IDE support
- Minimal dependencies

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Basic usage from command line:

```bash
python main.py https://example.com
```

### Command Line Options

- `--headless`: Run in headless mode
- `--timeout SECONDS`: Page load timeout in seconds (default: 30)
- `--window-size WIDTH,HEIGHT`: Set browser window size (default: 1920,1080)

### Programmatic Usage

```python
from core.browser import ChromeBrowser
from core.config import ChromeConfig

# Create a configuration
config = ChromeConfig(
    headless=True,
    window_size="1366,768",
    page_load_timeout=30
)

# Use the browser
with ChromeBrowser(config=config) as browser:
    browser.get("https://example.com")
    print(f"Page title: {browser.title}")
```

## License

MIT
