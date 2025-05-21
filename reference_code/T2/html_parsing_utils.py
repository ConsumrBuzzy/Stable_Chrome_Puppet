"""
html_parsing_utils.py

Utility functions for advanced HTML parsing using BeautifulSoup, designed for use with Selenium-rendered pages.

Best practice: Use Selenium to navigate and render the page, then pass driver.page_source to these utilities for robust, Pythonic extraction.
"""
from bs4 import BeautifulSoup
from typing import List, Optional

def parse_table_rows(html: str, table_selector: str) -> List[str]:
    """
    Parses all rows from a table in the given HTML using the provided CSS selector.
    Returns a list of row texts.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one(table_selector)
    if not table:
        return []
    return [row.get_text(strip=True) for row in table.select("tr")]

def extract_elements(html: str, css_selector: str) -> List[str]:
    """
    Extracts text from all elements matching the CSS selector in the given HTML.
    Returns a list of texts.
    """
    soup = BeautifulSoup(html, "html.parser")
    return [el.get_text(strip=True) for el in soup.select(css_selector)]

def extract_element_attribute(html: str, css_selector: str, attribute: str) -> List[str]:
    """
    Extracts the specified attribute from all elements matching the CSS selector.
    Returns a list of attribute values.
    """
    soup = BeautifulSoup(html, "html.parser")
    return [el.get(attribute, "") for el in soup.select(css_selector)]
