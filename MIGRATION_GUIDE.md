# Migration Guide: Browser Module Refactoring

This document outlines the changes made during the refactoring of the browser module and provides guidance on how to update your code to work with the new structure.

## Overview of Changes

The browser functionality has been refactored into a more modular and maintainable structure. The main changes include:

1. **Modular Structure**: The code is now split into logical modules based on functionality.
2. **Better Error Handling**: More specific exceptions and better error messages.
3. **Improved Type Hints**: Better type annotations throughout the codebase.
4. **Separation of Concerns**: Clearer separation between different aspects of browser automation.
5. **Enhanced Documentation**: Improved docstrings and module-level documentation.

## New Module Structure

```
core/browser/
├── __init__.py         # Package initialization and exports
├── base.py             # Base browser interface and utilities
├── chrome.py           # Chrome-specific implementation
├── element.py          # Element handling and interactions
├── exceptions.py       # Custom exceptions
├── navigation.py       # Page navigation and waiting
└── screenshot.py       # Screenshot functionality
```

## Key Changes

### 1. Imports

**Before:**
```python
from core.browser import ChromePuppet
```

**After:**
```python
from core.browser.chrome import ChromeBrowser
```

### 2. Browser Initialization

**Before:**
```python
from core.config import ChromeConfig

config = ChromeConfig()
browser = ChromePuppet(config)
```

**After:**
```python
from core.config import ChromeConfig
from core.browser import ChromeBrowser

config = ChromeConfig()
browser = ChromeBrowser(config)
```

### 3. Element Interaction

**Before:**
```python
element = browser.find_element(By.ID, "my-element")
element.click()
```

**After:**
```python
element_helper = browser.element  # If element helper is exposed as property
element = element_helper.find_element(By.ID, "my-element")
element_helper.click(element=element)

# Or use the direct WebElement method
element = browser.driver.find_element(By.ID, "my-element")
element.click()
```

### 4. Navigation

**Before:**
```python
browser.navigate_to("https://example.com")
```

**After:**
```python
browser.navigate_to("https://example.com")
# Or using the navigation mixin directly if available
browser.navigation.navigate_to("https://example.com")
```

### 5. Screenshots

**Before:**
```python
browser.take_screenshot("screenshot.png")
```

**After:**
```python
browser.screenshot.take_screenshot("screenshot.png")
```

## New Features

### 1. Better Error Handling

```python
try:
    element = element_helper.find_element(By.ID, "non-existent")
except ElementNotFoundError as e:
    print(f"Element not found: {e}")
```

### 2. Improved Waiting

```python
# Wait for an element to be visible
element = element_helper.wait_for_element_visible(
    By.ID, "my-element", 
    timeout=10.0
)

# Wait for URL to change
browser.navigation.wait_for_url_change(timeout=5.0)
```

### 3. Element Actions

```python
# Send keys with clearing first
element_helper.send_keys("my text", By.ID, "username")

# Click with retry
element_helper.click(By.CSS_SELECTOR, "button.primary")
```

## Migration Steps

1. Update your imports to use the new module structure.
2. Replace direct WebDriver method calls with the appropriate helper methods.
3. Update error handling to catch the new exception types.
4. Test thoroughly to ensure all functionality works as expected.

## Backward Compatibility

If you need to maintain backward compatibility, you can create a compatibility layer that provides the old interface while using the new implementation internally.

## Troubleshooting

If you encounter any issues during migration:
1. Check the error messages for hints about what needs to be updated.
2. Refer to the module documentation for the new API.
3. Look at the test cases for examples of how to use the new API.

## Next Steps

1. Update any documentation or examples that reference the old API.
2. Consider writing additional tests for any custom functionality.
3. Provide feedback on the new structure and any issues you encounter.
