# Agent Quick Reference

## Project Context

Chrome Puppet is a Python-based browser automation framework designed for stability and extensibility. It serves as a parent project for web automation tasks, providing robust Chrome/Chromium control through Selenium.

## Key Components (Memory Anchors)

1. **Core Modules**
   - `browser.py`: Main browser interface (legacy compatibility)
   - `core/browser/chrome.py`: Chrome implementation
   - `core/browser/element.py`: Element interaction utilities
   - `core/browser/navigation.py`: Page navigation and waiting
   - `core/browser/screenshot.py`: Screenshot functionality

2. **Important Classes**
   - `ChromeBrowser`: Main browser controller
   - `ElementHelper`: DOM element interactions
   - `NavigationMixin`: Page navigation utilities
   - `ScreenshotHelper`: Screenshot management

3. **Key Methods**
   - `ChromeBrowser.get(url)`: Navigate to URL
   - `ElementHelper.find_element()`: Locate elements
   - `NavigationMixin.wait_for_load()`: Wait for page load
   - `ScreenshotHelper.take_screenshot()`: Capture screenshots

## Quick Start (Agent Perspective)

```python
# Basic usage pattern
from core.browser.chrome import ChromeBrowser
from core.config import ChromeConfig

# Initialize with default config
config = ChromeConfig(headless=False)
browser = ChromeBrowser(config)

try:
    # Navigate and interact
    browser.get("https://example.com")
    
    # Find and interact with elements
    element = browser.element.find_element("css", "button.primary")
    browser.element.click(element)
    
    # Take screenshot
    browser.screenshot.take_screenshot("example.png")
    
finally:
    browser.close()
```

## Common Patterns

1. **Element Interaction**
   ```python
   # Wait for and click element
   elem = browser.element.wait_for_element("xpath", "//button[text()='Submit']")
   browser.element.click(elem)
   
   # Input text
   browser.element.send_keys("test@example.com", "css", "input[type='email']")
   ```

2. **Navigation**
   ```python
   # Wait for navigation
   browser.navigation.wait_for_url_contains("success")
   
   # Handle page loads
   browser.navigation.wait_for_page_load()
   ```

3. **Error Handling**
   ```python
   from core.browser.exceptions import ElementNotFoundError
   
   try:
       element = browser.element.find_element("id", "non-existent")
   except ElementNotFoundError as e:
       print(f"Element not found: {e}")
   ```

## Configuration Reference

### Environment Variables

```env
# Core Settings
HEADLESS=false  # Run browser in headless mode
WINDOW_WIDTH=1280
WINDOW_HEIGHT=1024
TIMEOUT=30  # Default timeout in seconds

# Paths
SCREENSHOT_DIR=./screenshots
DOWNLOAD_DIR=./downloads

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=./logs/chrome_puppet.log
```

### Chrome Options

Common Chrome options can be set via `ChromeConfig`:

```python
from core.config import ChromeConfig

config = ChromeConfig(
    headless=True,
    window_size=(1920, 1080),
    user_agent="Custom User Agent",
    disable_images=True,
    incognito=True
)
```

## Troubleshooting Guide

### Common Issues

1. **ChromeDriver Version Mismatch**
   - Symptom: `SessionNotCreatedException`
   - Fix: Ensure Chrome and ChromeDriver versions match
   - Command: `chromedriver --version` and `google-chrome --version`

2. **Element Not Found**
   - Check if in iframe: `browser.element.switch_to_iframe("iframe_name")
   - Add explicit wait: `browser.element.wait_for_element(selector, timeout=10)`

3. **Stale Element Reference**
   - Re-find element before interaction
   - Use retry pattern for dynamic content

### Debugging Tips

1. Enable debug logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. Take screenshot on error:
   ```python
   try:
       # Your code here
   except Exception as e:
       browser.screenshot.take_screenshot("error.png")
       raise
   ```

3. Check browser logs:
   ```python
   logs = browser.driver.get_log('browser')
   for entry in logs:
       print(entry)
   ```

## Performance Optimization

1. **Page Load Optimization**
   ```python
   # Disable images and CSS for faster loading
   config = ChromeConfig(
       disable_images=True,
       disable_css=True,
       disable_javascript=False
   )
   ```

2. **Parallel Execution**
   ```python
   # Use ThreadPoolExecutor for parallel tasks
   from concurrent.futures import ThreadPoolExecutor
   
   def process_url(url):
       with ChromeBrowser(config) as browser:
           browser.get(url)
           # Process page
   
   urls = ["https://example.com/1", "https://example.com/2"]
   with ThreadPoolExecutor(max_workers=3) as executor:
       executor.map(process_url, urls)
   ```

3. **Memory Management**
   - Use `browser.driver.quit()` instead of `close()` for complete cleanup
   - Clear cookies and cache between sessions if needed
   - Monitor memory usage with `import psutil; psutil.Process().memory_info().rss`

## Memory Management

1. **Session Management**
   - Always close browsers in `finally` blocks
   - Use context managers for automatic cleanup
   - Monitor open processes with `psutil`

2. **Resource Cleanup**
   ```python
   # Proper cleanup example
   try:
       # Your code here
   finally:
       try:
           if browser.driver:
               browser.driver.quit()
       except Exception as e:
           print(f"Error during cleanup: {e}")
   ```

## Integration Points

1. **Custom Extensions**
   ```python
   class CustomBrowser(ChromeBrowser):
       def custom_method(self):
           """Add custom functionality here."""
           pass
   ```

2. **Event Hooks**
   ```python
   # Add custom event listeners
   browser.driver.add_event_listener("click", lambda e: print(f"Clicked: {e}"))
   ```

## Security Notes

- Never log sensitive information
- Use environment variables for credentials
- Implement proper session management
- Validate all user inputs
- Keep dependencies updated
