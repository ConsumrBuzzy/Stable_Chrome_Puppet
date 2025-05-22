"""Network request/response interception."""
from typing import Dict, Any, Optional, Union, List, Callable, Tuple, TypeVar, cast
from functools import wraps
import json

from selenium.webdriver import Chrome
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.options import Options as ChromeOptions

from .request import Request, RequestInterceptorMixin
from .response import Response, ResponseInterceptorMixin

T = TypeVar('T', bound=Callable)

class NetworkInterceptorMixin(RequestInterceptorMixin, ResponseInterceptorMixin):
    """Mixin class providing network interception capabilities."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the network interceptor."""
        super().__init__(*args, **kwargs)
        self._interception_enabled = False
    
    def enable_network_interception(self) -> None:
        """Enable network request/response interception."""
        if not hasattr(self, 'driver') or not self.driver:
            raise RuntimeError("Cannot enable network interception: driver not initialized")
        
        # Enable network interception in Chrome DevTools Protocol
        self.driver.execute_cdp_cmd('Network.enable', {})
        
        # Set up request interception
        self.driver.execute_cdp_cmd(
            'Network.setRequestInterception',
            {'patterns': [{'urlPattern': '*'}]}
        )
        
        # Set up request/response listeners
        self.driver.execute_script("""
        window.interceptedRequests = [];
        
        const originalOpen = XMLHttpRequest.prototype.open;
        const originalSend = XMLHttpRequest.prototype.send;
        
        XMLHttpRequest.prototype.open = function(method, url) {
            this._method = method;
            this._url = url;
            return originalOpen.apply(this, arguments);
        };
        
        XMLHttpRequest.prototype.send = function(body) {
            const request = {
                method: this._method,
                url: this._url,
                headers: {},
                body: body
            };
            
            // Add request headers
            for (const [key, value] of Object.entries(this._headers || {})) {
                request.headers[key] = value;
            }
            
            window.interceptedRequests.push(request);
            return originalSend.apply(this, arguments);
        };
        
        const originalFetch = window.fetch;
        window.fetch = function(resource, init) {
            const request = {
                method: (init?.method || 'GET').toUpperCase(),
                url: resource instanceof Request ? resource.url : resource,
                headers: {},
                body: init?.body
            };
            
            // Add request headers
            if (init?.headers) {
                if (init.headers instanceof Headers) {
                    init.headers.forEach((value, key) => {
                        request.headers[key] = value;
                    });
                } else if (Array.isArray(init.headers)) {
                    init.headers.forEach(([key, value]) => {
                        request.headers[key] = value;
                    });
                } else {
                    Object.assign(request.headers, init.headers);
                }
            }
            
            window.interceptedRequests.push(request);
            return originalFetch(resource, init);
        };
        """)
        
        self._interception_enabled = True
    
    def disable_network_interception(self) -> None:
        """Disable network request/response interception."""
        if not hasattr(self, 'driver') or not self.driver:
            return
            
        if hasattr(self, '_interception_enabled') and self._interception_enabled:
            self.driver.execute_cdp_cmd('Network.disable', {})
            self._interception_enabled = False
    
    def get_intercepted_requests(self) -> List[Dict[str, Any]]:
        """Get all intercepted network requests.
        
        Returns:
            List of intercepted requests with their details
        """
        if not hasattr(self, 'driver') or not self.driver:
            return []
            
        return self.driver.execute_script("return window.interceptedRequests || [];")
    
    def clear_intercepted_requests(self) -> None:
        """Clear the list of intercepted requests."""
        if hasattr(self, 'driver') and self.driver:
            self.driver.execute_script("window.interceptedRequests = [];")
    
    def wait_for_request(
        self,
        url_pattern: str,
        timeout: float = 10,
        poll_frequency: float = 0.5
    ) -> Dict[str, Any]:
        """Wait for a request matching the URL pattern.
        
        Args:
            url_pattern: Pattern to match in the request URL
            timeout: Maximum time to wait in seconds
            poll_frequency: How often to check for the request
            
        Returns:
            The matching request details
            
        Raises:
            TimeoutError: If no matching request is found within the timeout
        """
        import time
        import re
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            requests = self.get_intercepted_requests()
            for request in requests:
                if re.search(url_pattern, request.get('url', '')):
                    return request
            time.sleep(poll_frequency)
        
        raise TimeoutError(f"Timed out waiting for request matching pattern: {url_pattern}")
