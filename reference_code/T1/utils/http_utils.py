"""
http_utils.py
Utility functions for HTTP requests using requests.
Follows PEP8, DRY, KISS, and SOLID principles.
"""
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def get_session_with_retries(total_retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    """Return a requests.Session with retry logic."""
    session = requests.Session()
    retries = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def http_get(url, params=None, headers=None, timeout=10, log_errors=True):
    """Perform a GET request with retries and logging."""
    session = get_session_with_retries()
    try:
        response = session.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
    except Exception as e:
        if log_errors:
            logging.error(f"[http_utils] GET request failed: {url} | {e}")
        return None


def http_post(url, data=None, json=None, headers=None, timeout=10, log_errors=True):
    """Perform a POST request with retries and logging."""
    session = get_session_with_retries()
    try:
        response = session.post(url, data=data, json=json, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
    except Exception as e:
        if log_errors:
            logging.error(f"[http_utils] POST request failed: {url} | {e}")
        return None
