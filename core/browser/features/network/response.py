"""Network response handling."""
from typing import Dict, Any, Optional, Union, List, Tuple, Callable
from dataclasses import dataclass

@dataclass
class Response:
    """Represents an HTTP response."""
    
    status_code: int
    url: str
    headers: Dict[str, str]
    body: Optional[Union[Dict[str, Any], str, bytes]] = None
    
    @property
    def ok(self) -> bool:
        """Check if the response status code is successful (2xx)."""
        return 200 <= self.status_code < 300
    
    @classmethod
    def from_selenium_response(cls, response: Any) -> 'Response':
        """Create a Response from a Selenium response object.
        
        Args:
            response: The Selenium response object
            
        Returns:
            A new Response instance
        """
        return cls(
            status_code=response.status,
            url=response.url,
            headers=dict(response.headers),
            body=getattr(response, 'body', None)
        )

class ResponseInterceptorMixin:
    """Mixin class for intercepting and modifying network responses."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the response interceptor."""
        super().__init__(*args, **kwargs)
        self._response_interceptors: List[Callable[[Response], Optional[Response]]] = []
    
    def add_response_interceptor(self, interceptor: Callable[[Response], Optional[Response]]) -> None:
        """Add a response interceptor function.
        
        The interceptor function should accept a Response object and return a modified Response
        or None to block the response.
        
        Args:
            interceptor: Function that takes a Response and returns a modified Response or None
        """
        self._response_interceptors.append(interceptor)
    
    def remove_response_interceptor(self, interceptor: Callable[[Response], Optional[Response]]) -> None:
        """Remove a response interceptor function.
        
        Args:
            interceptor: The interceptor function to remove
        """
        if interceptor in self._response_interceptors:
            self._response_interceptors.remove(interceptor)
    
    def clear_response_interceptors(self) -> None:
        """Remove all response interceptors."""
        self._response_interceptors.clear()
    
    def _process_response_interceptors(self, response: Response) -> Optional[Response]:
        """Process a response through all registered interceptors.
        
        Args:
            response: The response to process
            
        Returns:
            The modified response or None if the response should be blocked
        """
        modified_response = response
        for interceptor in self._response_interceptors:
            result = interceptor(modified_response)
            if result is None:
                return None
            modified_response = result
        return modified_response
