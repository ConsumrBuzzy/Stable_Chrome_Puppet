"""
Configuration settings and environment variable support for DNC automation.
Uses Pydantic for settings management and python-dotenv for .env support.
"""
import os
import logging
from pathlib import Path
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    # Application settings
    APP_NAME: str = "DNC Genie"
    LOG_LEVEL: str = "INFO"
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 5  # Number of requests
    RATE_LIMIT_PERIOD: float = 1.0  # Time period in seconds
    
    # Zoom credentials
    ZOOM_EMAIL: str = Field(..., env="ZOOM_EMAIL")
    ZOOM_PASSWORD: str = Field(..., env="ZOOM_PASSWORD")
    
    # For backward compatibility
    ZOOM_USERNAME: Optional[str] = Field(None, env="ZOOM_USERNAME")
    
    # Timeouts and waits
    DEFAULT_WAIT: int = 10  # seconds
    PAGE_LOAD_TIMEOUT: int = 30  # seconds
    
    # URLs
    ZOOM_SIGNIN_URL: str = "https://zoom.us/signin#/login"
    DNC_MANAGEMENT_URL: str = "https://zoom.us/cci/index/admin#/admin-preferences"
    WORKPLACE_DNC_URL: str = "https://zoom.us/pbx/page/telephone/Settings#/settings/blocked-list?page_number=1&page_size=15"
    
    # For backward compatibility
    ZOOM_WORKPLACE_URL: str = WORKPLACE_DNC_URL
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
    
    @validator('ZOOM_USERNAME', pre=True, always=True)
    def set_zoom_username(cls, v, values):
        """Set ZOOM_USERNAME from ZOOM_EMAIL if not explicitly set."""
        if v is None:
            return values.get('ZOOM_EMAIL')
        return v

# Create settings instance
settings = Settings()

def setup_logging() -> logging.Logger:
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "dnc_genie.log", encoding='utf-8')
        ]
    )
    
    # Create and return logger for this module
    logger = logging.getLogger(settings.APP_NAME)
    logger.info("Logging configured")
    return logger
