"""
parse_html_and_logs.py

Utility functions for parsing HTML and log files to extract error messages, banners, and important UI state for diagnostics.

Usage:
    python parse_html_and_logs.py <html_file_or_log_file>

Dependencies:
    pip install beautifulsoup4
"""
import sys
import os
from bs4 import BeautifulSoup
import re

def extract_errors_from_html(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    banners = []
    # Common error banners and alerts
    for cls in ['alert', 'error', 'banner', 'warning', 'message', 'notice']:
        banners += [el.get_text(strip=True) for el in soup.find_all(class_=re.compile(cls, re.I))]
    # Also check for visible divs/spans with suspicious text
    for el in soup.find_all(['div', 'span']):
        txt = el.get_text(strip=True)
        if any(word in txt.lower() for word in ['error', 'failed', 'invalid', 'captcha', 'try again', 'locked', 'denied']):
            banners.append(txt)
    return banners

def extract_errors_from_log(log_path):
    errors = []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if re.search(r'(error|failed|exception|denied|locked|captcha|timeout|not found)', line, re.I):
                errors.append(line.strip())
    return errors

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_html_and_logs.py <html_file_or_log_file>")
        return
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    if path.lower().endswith('.html'):
        banners = extract_errors_from_html(path)
        print("\n--- Extracted Error/Warning Banners from HTML ---")
        for b in banners:
            print(b)
    else:
        errors = extract_errors_from_log(path)
        print("\n--- Extracted Errors/Warnings from Log ---")
        for e in errors:
            print(e)

if __name__ == "__main__":
    main()
