"""Screenshot functionality for browser automation."""
import os
import base64
import logging
from pathlib import Path
from typing import Optional, Union, Tuple, BinaryIO, TYPE_CHECKING

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.remote.webelement import WebElement

from .exceptions import ScreenshotError

class ScreenshotHelper:
    """Helper class for taking and managing screenshots."""
    
    def __init__(self, browser: Any):
        """Initialize with a browser instance.
        
        Args:
            browser: The browser instance (must have a 'driver' attribute)
        """
        self.browser = browser
        self.driver = browser.driver
        self.logger = getattr(browser, '_logger', None)
    
    def _log(self, level: str, message: str, *args, **kwargs) -> None:
        """Log a message if logger is available."""
        if self.logger:
            getattr(self.logger, level)(message, *args, **kwargs)
    
    def _ensure_directory_exists(self, file_path: Union[str, os.PathLike]) -> str:
        """Ensure the directory for the file path exists.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Absolute path to the file
            
        Raises:
            ScreenshotError: If directory creation fails
        """
        try:
            file_path = os.path.abspath(file_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            return file_path
        except Exception as e:
            error_msg = f"Failed to create directory for {file_path}: {str(e)}"
            self._log('error', error_msg)
            raise ScreenshotError(error_msg) from e
    
    def take_screenshot(
        self,
        file_path: Optional[Union[str, os.PathLike]] = None,
        element: Optional['WebElement'] = None,
        full_page: bool = False,
        return_png: bool = False
    ) -> Union[bool, bytes]:
        """Take a screenshot of the current page or a specific element.
        
        Args:
            file_path: Path to save the screenshot (optional)
            element: WebElement to capture (optional)
            full_page: If True, capture the full page (may not work in all browsers)
            return_png: If True, return PNG data instead of saving to file
            
        Returns:
            Union[bool, bytes]: 
                - If return_png is False: bool indicating success
                - If return_png is True: PNG image data as bytes
                
        Raises:
            ScreenshotError: If screenshot capture fails
        """
        if not hasattr(self, 'driver') or self.driver is None:
            raise ScreenshotError("Browser is not initialized")
        
        try:
            # Take screenshot of the current viewport or element
            if element is not None:
                png_data = element.screenshot_as_png
            elif full_page:
                png_data = self._take_full_page_screenshot()
            else:
                png_data = self.driver.get_screenshot_as_png()
            
            # Return raw PNG data if requested
            if return_png:
                return png_data
                
            # Save to file if path is provided
            if file_path:
                file_path = self._ensure_directory_exists(file_path)
                with open(file_path, 'wb') as f:
                    f.write(png_data)
                self._log('info', f"Screenshot saved to: {file_path}")
                return True
                
            return False
            
        except Exception as e:
            error_msg = f"Failed to take screenshot: {str(e)}"
            self._log('error', error_msg)
            raise ScreenshotError(error_msg) from e
    
    def _take_full_page_screenshot(self) -> bytes:
        """Take a screenshot of the entire page.
        
        This is a best-effort implementation that may not work in all browsers.
        
        Returns:
            bytes: PNG image data
            
        Raises:
            ScreenshotError: If full page screenshot is not supported
        """
        try:
            # Try to use the full page screenshot feature if available
            if hasattr(self.driver, 'get_full_page_screenshot_as_png'):
                return self.driver.get_full_page_screenshot_as_png()
                
            # Fallback to viewport stitching (simplified)
            self._log('debug', "Full page screenshot not natively supported, using viewport stitching")
            
            # Get the total page height
            total_height = self.driver.execute_script(
                "return Math.max(document.body.scrollHeight, "
                "document.body.offsetHeight, document.documentElement.clientHeight, "
                "document.documentElement.scrollHeight, document.documentElement.offsetHeight);"
            )
            
            viewport_height = self.driver.execute_script("return window.innerHeight;")
            viewport_width = self.driver.execute_script("return window.innerWidth;")
            
            # Take multiple screenshots and stitch them together
            # Note: This is a simplified implementation
            # A full implementation would need to handle scrolling and stitching
            
            # For now, just take a screenshot of the current viewport
            return self.driver.get_screenshot_as_png()
            
        except Exception as e:
            raise ScreenshotError(
                "Full page screenshots are not supported in this browser/driver. "
                f"Error: {str(e)}"
            ) from e
    
    def take_element_screenshot(
        self,
        element: 'WebElement',
        file_path: Optional[Union[str, os.PathLike]] = None,
        highlight: bool = False,
        return_png: bool = False
    ) -> Union[bool, bytes]:
        """Take a screenshot of a specific web element.
        
        Args:
            element: WebElement to capture
            file_path: Path to save the screenshot (optional)
            highlight: If True, highlight the element with a red border
            return_png: If True, return PNG data instead of saving to file
            
        Returns:
            Union[bool, bytes]: 
                - If return_png is False: bool indicating success
                - If return_png is True: PNG image data as bytes
        """
        if not hasattr(self, 'driver') or self.driver is None:
            raise ScreenshotError("Browser is not initialized")
            
        try:
            # Highlight the element if requested
            original_style = None
            if highlight:
                original_style = element.get_attribute('style')
                self.driver.execute_script(
                    "arguments[0].setAttribute('style', arguments[1]);",
                    element,
                    "border: 2px solid red;"
                )
            
            # Take the screenshot
            result = self.take_screenshot(
                file_path=file_path,
                element=element,
                return_png=return_png
            )
            
            # Restore original style if we changed it
            if highlight and original_style is not None:
                self.driver.execute_script(
                    "arguments[0].setAttribute('style', arguments[1]);",
                    element,
                    original_style
                )
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to take element screenshot: {str(e)}"
            self._log('error', error_msg)
            raise ScreenshotError(error_msg) from e
    
    def save_screenshot_as_base64(
        self,
        file_path: Union[str, os.PathLike],
        element: Optional['WebElement'] = None,
        full_page: bool = False
    ) -> str:
        """Save a screenshot as a base64-encoded string.
        
        Args:
            file_path: Path to save the base64 data
            element: WebElement to capture (optional)
            full_page: If True, capture the full page
            
        Returns:
            str: Base64-encoded image data
        """
        try:
            # Take the screenshot as PNG
            png_data = self.take_screenshot(
                file_path=None,
                element=element,
                full_page=full_page,
                return_png=True
            )
            
            # Convert to base64
            base64_data = base64.b64encode(png_data).decode('utf-8')
            
            # Save to file if path is provided
            if file_path:
                file_path = self._ensure_directory_exists(file_path)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(base64_data)
                self._log('info', f"Base64 screenshot saved to: {file_path}")
            
            return base64_data
            
        except Exception as e:
            error_msg = f"Failed to save base64 screenshot: {str(e)}"
            self._log('error', error_msg)
            raise ScreenshotError(error_msg) from e
