"""Cookie management functionality."""
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

@dataclass
class Cookie:
    """Represents an HTTP cookie."""
    
    name: str
    value: str
    domain: Optional[str] = None
    path: Optional[str] = None
    secure: bool = False
    http_only: bool = False
    expiry: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the cookie to a dictionary.
        
        Returns:
            Dictionary representation of the cookie
        """
        cookie_dict = {
            'name': self.name,
            'value': self.value,
            'secure': self.secure,
            'httpOnly': self.http_only
        }
        
        if self.domain:
            cookie_dict['domain'] = self.domain
        if self.path:
            cookie_dict['path'] = self.path
        if self.expiry is not None:
            cookie_dict['expiry'] = self.expiry
            
        return cookie_dict
    
    @classmethod
    def from_dict(cls, cookie_dict: Dict[str, Any]) -> 'Cookie':
        """Create a Cookie from a dictionary.
        
        Args:
            cookie_dict: Dictionary containing cookie attributes
            
        Returns:
            A new Cookie instance
        """
        return cls(
            name=cookie_dict['name'],
            value=cookie_dict['value'],
            domain=cookie_dict.get('domain'),
            path=cookie_dict.get('path'),
            secure=cookie_dict.get('secure', False),
            http_only=cookie_dict.get('httpOnly', False),
            expiry=cookie_dict.get('expiry')
        )

class CookieManagerMixin:
    """Mixin class providing cookie management functionality."""
    
    def get_cookies(self) -> List[Cookie]:
        """Get all cookies.
        
        Returns:
            List of Cookie objects
        """
        return [
            Cookie.from_dict(cookie_dict)
            for cookie_dict in self.driver.get_cookies()
        ]
    
    def get_cookie(self, name: str) -> Optional[Cookie]:
        """Get a cookie by name.
        
        Args:
            name: Name of the cookie to get
            
        Returns:
            The Cookie object or None if not found
        """
        cookie_dict = self.driver.get_cookie(name)
        if not cookie_dict:
            return None
        return Cookie.from_dict(cookie_dict)
    
    def add_cookie(self, cookie: Union[Cookie, Dict[str, Any]]) -> None:
        """Add a cookie.
        
        Args:
            cookie: Cookie object or dictionary with cookie attributes
        """
        if isinstance(cookie, Cookie):
            cookie_dict = cookie.to_dict()
        else:
            cookie_dict = cookie
        
        self.driver.add_cookie(cookie_dict)
    
    def delete_cookie(self, name: str) -> None:
        """Delete a cookie by name.
        
        Args:
            name: Name of the cookie to delete
        """
        self.driver.delete_cookie(name)
    
    def delete_all_cookies(self) -> None:
        """Delete all cookies."""
        self.driver.delete_all_cookies()
    
    def get_cookie_value(self, name: str) -> Optional[str]:
        """Get the value of a cookie by name.
        
        Args:
            name: Name of the cookie
            
        Returns:
            The cookie value or None if not found
        """
        cookie = self.get_cookie(name)
        return cookie.value if cookie else None
    
    def set_cookie_value(
        self,
        name: str,
        value: str,
        domain: Optional[str] = None,
        path: str = '/',
        secure: bool = False,
        http_only: bool = False,
        expiry: Optional[int] = None
    ) -> None:
        """Set a cookie value.
        
        Args:
            name: Cookie name
            value: Cookie value
            domain: Cookie domain (default: current domain)
            path: Cookie path (default: '/')
            secure: Whether the cookie is secure (default: False)
            http_only: Whether the cookie is HTTP only (default: False)
            expiry: Expiry time as a Unix timestamp (default: None for session cookie)
        """
        cookie = Cookie(
            name=name,
            value=value,
            domain=domain,
            path=path,
            secure=secure,
            http_only=http_only,
            expiry=expiry
        )
        self.add_cookie(cookie)
