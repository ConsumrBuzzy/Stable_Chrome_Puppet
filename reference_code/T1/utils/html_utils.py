"""
html_utils.py
Utility functions for parsing HTML using BeautifulSoup (bs4).
Follows PEP8, DRY, KISS, and SOLID principles.
"""
from bs4 import BeautifulSoup
import logging


def parse_html(html):
    """Parse HTML and return a BeautifulSoup object."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        return soup
    except Exception as e:
        logging.error(f"[html_utils] Failed to parse HTML: {e}")
        return None


def extract_text_by_selector(html, selector):
    """Extract text from HTML using a CSS selector."""
    soup = parse_html(html)
    if not soup:
        return []
    try:
        elements = soup.select(selector)
        return [el.get_text(strip=True) for el in elements]
    except Exception as e:
        logging.error(f"[html_utils] Selector extraction failed: {e}")
        return []


def extract_error_banners(html):
    """Extract common error banner texts from HTML (customize as needed)."""
    soup = parse_html(html)
    if not soup:
        return []
    banners = []
    for cls in [
        '.error', '.alert', '.banner', '.notification', '.warning', '.msg', '.message', '.danger', '.toast',
        '.MuiAlert-message', '.ant-alert-message', '.alert-danger', '.alert-warning']:
        banners.extend([el.get_text(strip=True) for el in soup.select(cls)])
    return banners
