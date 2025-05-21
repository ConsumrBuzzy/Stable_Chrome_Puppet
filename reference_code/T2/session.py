"""
Session management for DNC Genie.
Handles authentication state, session persistence, and timeouts.
"""
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from config import settings

logger = logging.getLogger(__name__)

class ZoomSession:
    """Manages Zoom authentication session state and persistence."""
    
    SESSION_FILE = Path(".zoom_session.json")
    SESSION_TIMEOUT = timedelta(hours=4)  # Zoom sessions typically expire after 4 hours
    
    def __init__(self):
        self._session_data: Dict[str, Any] = {}
        self._loaded = False
        self._dirty = False
    
    @property
    def is_authenticated(self) -> bool:
        """Check if there's a valid authenticated session."""
        if not self._loaded:
            self._load_session()
            
        if not self._session_data.get("authenticated"):
            return False
            
        # Check session expiration
        expires_at = self._session_data.get("expires_at")
        if expires_at and datetime.fromisoformat(expires_at) < datetime.utcnow():
            logger.info("Session has expired")
            return False
            
        return True
    
    def create_session(self, user_data: Dict[str, Any]) -> None:
        """Create a new authenticated session."""
        self._session_data = {
            "authenticated": True,
            "user_id": user_data.get("user_id"),
            "email": user_data.get("email"),
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + self.SESSION_TIMEOUT).isoformat(),
            "token": user_data.get("token"),
            "refresh_token": user_data.get("refresh_token"),
        }
        self._dirty = True
        self._save_session()
        logger.info("Created new authenticated session")
    
    def invalidate(self) -> None:
        """Invalidate the current session."""
        if self.SESSION_FILE.exists():
            self.SESSION_FILE.unlink()
        self._session_data = {}
        self._dirty = False
        logger.info("Session invalidated")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        if not self.is_authenticated:
            raise AuthenticationError("Not authenticated")
            
        return {
            "Authorization": f"Bearer {self._session_data.get('token')}",
            "Content-Type": "application/json"
        }
    
    def refresh(self) -> bool:
        """Attempt to refresh the session."""
        # TODO: Implement token refresh logic
        # For now, just extend the expiration
        if self.is_authenticated:
            self._session_data["expires_at"] = (datetime.utcnow() + self.SESSION_TIMEOUT).isoformat()
            self._dirty = True
            self._save_session()
            return True
        return False
    
    def _load_session(self) -> None:
        """Load session data from disk."""
        if self._loaded:
            return
            
        if not self.SESSION_FILE.exists():
            self._session_data = {}
            self._loaded = True
            return
            
        try:
            with open(self.SESSION_FILE, 'r', encoding='utf-8') as f:
                self._session_data = json.load(f)
            self._loaded = True
            logger.debug("Loaded session from disk")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load session: {e}")
            self._session_data = {}
            self._loaded = True
    
    def _save_session(self) -> None:
        """Save session data to disk."""
        if not self._dirty:
            return
            
        try:
            with open(self.SESSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._session_data, f, indent=2)
            self._dirty = False
            logger.debug("Saved session to disk")
        except IOError as e:
            logger.error(f"Failed to save session: {e}")

    def requires_auth(self, func):
        """Decorator to ensure the user is authenticated."""
        from .exceptions import AuthenticationError  # Local import to avoid circular import
        def wrapper(*args, **kwargs):
            if not self.is_authenticated:
                raise AuthenticationError("Authentication required")
            return func(*args, **kwargs)
        return wrapper

# Global session instance
session = ZoomSession()
