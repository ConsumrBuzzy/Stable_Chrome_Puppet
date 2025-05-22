"""Network request handling."""
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass

@dataclass
class Request:
    """Represents an HTTP request."""
    
    method: str
    url: str
    headers: Dict[str, str]
    post_data: Optional[Union[Dict[str, Any], str]] = None
    
    @classmethod
    def from_selenium_request(cls, request: Any) -> 'Request':
        """Create a Request from a Selenium request object.
        
        Args:
            request: The Selenium request object
            
        Returns:
            A new Request instance
        """
        return cls(
            method=request.method,
            url=request.url,
            headers=dict(request.headers),
            post_data=getattr(request, 'post_data', None)
        )

class RequestInterceptorMixin:
    """Mixin class for intercepting and modifying network requests."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the request interceptor."""
        super().__init__(*args, **kwargs)
        self._request_interceptors: List[callable] = []
    
    def add_request_interceptor(self, interceptor: callable) -> None:
        """Add a request interceptor function.
        
        The interceptor function should accept a Request object and return a modified Request
        or None to block the request.
        
        Args:
            interceptor: Function that takes a Request and returns a modified Request or None
        """
        self._request_interceptors.append(interceptor)
    
    def remove_request_interceptor(self, interceptor: callable) -> None:
        """Remove a request interceptor function.
        
        Args:
            interceptor: The interceptor function to remove
        """
        if interceptor in self._request_interceptors:
            self._request_interceptors.remove(interceptor)
    
    def clear_request_interceptors(self) -> None:
        """Remove all request interceptors."""
        self._request_interceptors.clear()
    
    def _process_request_interceptors(self, request: Request) -> Optional[Request]:
        """Process a request through all registered interceptors.
        
        Args:
            request: The request to process
            
        Returns:
            The modified request or None if the request should be blocked
        """
        modified_request = request
        for interceptor in self._request_interceptors:
            result = interceptor(modified_request)
            if result is None:
                return None
            modified_request = result
        return modified_request
