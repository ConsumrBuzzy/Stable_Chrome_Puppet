"""
env_utils.py
Utility functions for environment variable and credential loading for DNC Genie.
Inspired by T1 reference.
"""
import os
import sys
import logging
from typing import Optional
from getpass import getpass
from dotenv import load_dotenv
from colorama import Fore, Style

# Configure logger
logger = logging.getLogger(__name__)

def load_credentials():
    """Load Zoom credentials from .env file and validate. Compatible with both ZOOM_EMAIL and ZOOM_USERNAME."""
    load_dotenv()
    # Support both naming conventions for compatibility
    email = os.getenv("ZOOM_EMAIL") or os.getenv("ZOOM_USERNAME")
    password = os.getenv("ZOOM_PASSWORD")
    missing = []
    if not email:
        missing.append("ZOOM_EMAIL or ZOOM_USERNAME")
    if not password:
        missing.append("ZOOM_PASSWORD")
    if missing:
        print(Fore.RED + f"Missing required environment variables: {', '.join(missing)}.\nPlease set them in your .env file." + Style.RESET_ALL)
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    return email, password


def get_env_variable(name: str, default: Optional[str] = None) -> str:
    """
    Get an environment variable or return a default value.
    
    Args:
        name: Name of the environment variable
        default: Default value to return if variable is not set
        
    Returns:
        str: The value of the environment variable or default value
        
    Raises:
        ValueError: If the variable is not set and no default is provided
    """
    value = os.getenv(name, default)
    if value is None:
        error_msg = f"Environment variable {name} is not set"
        logger.error(error_msg)
        raise ValueError(error_msg)
    return value


def get_secure_env_variable(name: str, prompt: Optional[str] = None) -> str:
    """
    Get a sensitive environment variable, prompting the user if not set.
    
    Args:
        name: Name of the environment variable
        prompt: Custom prompt to display when asking for input
        
    Returns:
        str: The value of the environment variable or user input
    """
    value = os.getenv(name)
    if not value:
        prompt = prompt or f"Please enter {name} (input will be hidden): "
        value = getpass(prompt)
    return value


def load_environment() -> None:
    """Load environment variables from .env file if it exists."""
    if load_dotenv():
        logger.debug("Loaded environment variables from .env file")
    else:
        logger.debug("No .env file found, using system environment variables")
