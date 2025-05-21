# Chrome Puppet Examples

This document provides practical examples of using Chrome Puppet for browser automation.

## Table of Contents

- [Basic Browser Usage](#basic-browser-usage)
- [Taking Screenshots](#taking-screenshots)
- [Handling Forms](#handling-forms)
- [Working with Tabs](#working-with-tabs)
- [Advanced Configuration](#advanced-configuration)
- [Error Handling](#error-handling)
- [Using Custom Chrome Options](#using-custom-chrome-options)
- [Page Object Model Example](#page-object-model-example)
- [Best Practices](#best-practices)

## Basic Browser Usage

```python
from chrome_puppet import ChromePuppet, ChromeConfig

# Initialize with default settings
config = ChromeConfig(
    headless=False,  # Set to True for headless mode
    window_size=(1366, 768)
)

with ChromePuppet(config=config) as browser:
    # Navigate to a website
    browser.get("https://example.com")
    
    # Get page title
    print(f"Page title: {browser.driver.title}")
    
    # Get page source
    page_source = browser.driver.page_source
    print(f"Page source length: {len(page_source)} bytes")
```

## Taking Screenshots

```python
from chrome_puppet import ChromePuppet

with ChromePuppet() as browser:
    browser.get("https://example.com")
    
    # Take full page screenshot
    browser.save_screenshot("full_page.png")
    
    # Take screenshot with custom viewport size
    browser.driver.set_window_size(800, 600)
    browser.save_screenshot("custom_viewport.png")
```

## Handling Forms

```python
from chrome_puppet import ChromePuppet
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

with ChromePuppet() as browser:
    browser.get("https://example.com/login")
    
    # Find and fill form fields
    username = browser.driver.find_element(By.NAME, "username")
    password = browser.driver.find_element(By.NAME, "password")
    
    username.send_keys("testuser")
    password.send_keys("securepassword")
    
    # Submit the form
    browser.driver.find_element(By.TAG_NAME, "form").submit()
    
    # Wait for login to complete
    WebDriverWait(browser.driver, 10).until(
        EC.url_contains("dashboard")
    )
```

## Working with Tabs

```python
from chrome_puppet import ChromePuppet

with ChromePuppet() as browser:
    # Open a new tab
    browser.driver.execute_script("window.open('about:blank', 'tab2');")
    
    # Switch to the new tab
    browser.driver.switch_to.window("tab2")
    browser.get("https://example.org")
    
    # Switch back to the first tab
    browser.driver.switch_to.window(browser.driver.window_handles[0])
```

## Advanced Configuration

```python
from chrome_puppet import ChromePuppet, ChromeConfig

# Custom configuration
config = ChromeConfig(
    headless=True,
    window_size=(1920, 1080),
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    disable_images=True,
    disable_javascript=False,
    proxy="socks5://127.0.0.1:9050"
)

with ChromePuppet(config=config) as browser:
    browser.get("https://example.com")
    print(f"Page loaded with custom config: {browser.driver.title}")
```

## Error Handling

```python
from chrome_puppet import ChromePuppet
from selenium.common.exceptions import TimeoutException

try:
    with ChromePuppet() as browser:
        # Set a short timeout for demonstration
        browser.driver.set_page_load_timeout(5)
        
        # This will likely timeout
        browser.get("https://example.com")
        
except TimeoutException:
    print("Page load timed out!")
    
# Browser is automatically closed by the context manager
```

## Using Custom Chrome Options

```python
from chrome_puppet import ChromePuppet, ChromeConfig
from selenium.webdriver.chrome.options import Options

# Create custom Chrome options
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Create config with custom options
config = ChromeConfig(
    headless=True,
    chrome_options=chrome_options
)

with ChromePuppet(config=config) as browser:
    browser.get("https://example.com")
    print(f"Page title: {browser.driver.title}")
```

## Page Object Model Example

```python
from chrome_puppet import ChromePuppet
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        self.url = "https://example.com/login"
    
    def load(self):
        self.driver.get(self.url)
        return self
    
    def login(self, username, password):
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        self.driver.find_element(By.TAG_NAME, "form").submit()
        return DashboardPage(self.driver)

class DashboardPage:
    def __init__(self, driver):
        self.driver = driver
    
    def is_displayed(self):
        return "dashboard" in self.driver.current_url

# Usage
with ChromePuppet() as browser:
    login_page = LoginPage(browser.driver).load()
    dashboard = login_page.login("testuser", "password123")
    
    if dashboard.is_displayed():
        print("Login successful!")
    else:
        print("Login failed!")
```

## Best Practices

1. **Always use context managers** (`with` statement) to ensure proper resource cleanup
2. **Use explicit waits** instead of hard-coded `time.sleep()` calls
3. **Handle errors gracefully** with appropriate try/except blocks
4. **Keep selectors maintainable** by using data attributes or IDs when possible
5. **Use Page Object Model** for better test organization and maintenance
6. **Clean up after tests** by closing all browser instances
7. **Use environment variables** for sensitive data like credentials
8. **Implement retry logic** for flaky operations
9. **Monitor resource usage** to prevent memory leaks
10. **Regularly update ChromeDriver** to match your Chrome version

```python
# Example of explicit wait
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "dynamic-element"))
)
```
   ```

3. **Handle errors gracefully** and provide meaningful error messages.
4. **Clean up** after your tests by closing all browser instances.
5. **Use page objects** for complex applications to improve test maintainability.
