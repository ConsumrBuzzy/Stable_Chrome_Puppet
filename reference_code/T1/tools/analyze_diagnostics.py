"""
analyze_diagnostics.py

Batch-analyze all HTML, log, and screenshot files in the shots/ directory using existing OCR and HTML/log parsers.
Summarizes errors, banners, and suspicious UI states for diagnostics.

Usage:
    python tools/analyze_diagnostics.py

Dependencies:
    pip install beautifulsoup4 pillow pytesseract
"""
import os
import sys
import re
from glob import glob
from PIL import Image
from datetime import datetime  # PEP8: direct import for datetime.now()
import pytesseract
from bs4 import BeautifulSoup

# Tesseract path setup (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'  # Update if needed

# Helper: Extract errors/warnings from HTML (same logic as parse_html_and_logs.py)
def extract_errors_from_html(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    banners = []
    for cls in ['alert', 'error', 'banner', 'warning', 'message', 'notice']:
        banners += [el.get_text(strip=True) for el in soup.find_all(class_=re.compile(cls, re.I))]
    for el in soup.find_all(['div', 'span']):
        txt = el.get_text(strip=True)
        if any(word in txt.lower() for word in ['error', 'failed', 'invalid', 'captcha', 'try again', 'locked', 'denied']):
            banners.append(txt)
    return banners

# Helper: Extract errors/warnings from logs
def extract_errors_from_log(log_path):
    errors = []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if re.search(r'(error|failed|exception|denied|locked|captcha|timeout|not found)', line, re.I):
                errors.append(line.strip())
    return errors

# Helper: OCR text from image
def ocr_image(img_path):
    try:
        img = Image.open(img_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        return f'OCR ERROR: {e}'

def get_last_run_window():
    """Return (start_time, end_time) as datetimes for the last run from run_times.log."""
    log_path = os.path.join(os.path.dirname(__file__), '..', 'shots', 'run_times.log')
    if not os.path.isfile(log_path):
        return None, None
    starts, ends = [], []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('start:'):
                starts.append(line.strip().split('start:')[1].strip())
            elif line.startswith('end:'):
                ends.append(line.strip().split('end:')[1].strip())
    if not starts or not ends:
        return None, None
    # Find the last start before the last end
    last_end = ends[-1]
    last_start = None
    for s in reversed(starts):
        if s < last_end:
            last_start = s
            break
    if not last_start:
        last_start = starts[-1]
    start_dt = datetime.fromisoformat(last_start)
    end_dt = datetime.fromisoformat(last_end)
    return start_dt, end_dt

def analyze_html_file(html_file):
    banners = extract_errors_from_html(html_file)
    section = f"--- {os.path.basename(html_file)}: HTML banners/warnings ---"
    output = section + '\n'
    for b in banners:
        output += f"  {b}\n"
    if not banners:
        output += "  (No error banners detected)\n"
    return output

def main():
    shots_dir = os.path.join(os.path.dirname(__file__), '..', 'shots')
    print(f"Analyzing diagnostics in {os.path.abspath(shots_dir)}...")

    # Only process files from the most recent run window
    start_dt, end_dt = get_last_run_window()
    if not start_dt or not end_dt:
        print("[Diagnostics] Could not determine last run window. Analyzing all files.")
        html_files = glob(os.path.join(shots_dir, '*.html'))
        png_files = glob(os.path.join(shots_dir, '*.png'))
    else:
        def in_window(f):
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(f))
                return start_dt <= mtime <= end_dt
            except Exception:
                return False
        html_files = [f for f in glob(os.path.join(shots_dir, '*.html')) if in_window(f)]
        png_files = [f for f in glob(os.path.join(shots_dir, '*.png')) if in_window(f)]
        print(f"[Diagnostics] Filtering files from {start_dt} to {end_dt} ({len(html_files)} HTML, {len(png_files)} PNG)")

    # Analyze HTML files
    html_results = []
    for html_file in html_files:
        html_results.append(analyze_html_file(html_file))

    # Analyze screenshots (OCR)
    ocr_results = []
    for png_file in png_files:
        try:
            img = Image.open(png_file)
            text = ocr_image(img)
            ocr_results.append((png_file, text))
        except Exception as e:
            ocr_results.append((png_file, f"OCR ERROR: {e}"))

    # Write summary log
    summary_path = os.path.join(shots_dir, f'diagnostics_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write('=== HTML Analysis Results ===\n')
        for res in html_results:
            f.write(res + '\n')
        f.write('\n=== Screenshot OCR Results ===\n')
        for fname, text in ocr_results:
            f.write(f'--- {os.path.basename(fname)}: OCR text ---\n{text}\n\n')
    print(f"\nDiagnostics summary saved to {summary_path}")

    # Analyze logs
    log_files = glob(os.path.join(shots_dir, '*.log')) + glob(os.path.join(shots_dir, '*.txt'))
    output_lines = []
    for log in log_files:
        errors = extract_errors_from_log(log)
        section = f"--- {os.path.basename(log)}: Log errors/warnings ---"
        output_lines.append(section)
        for e in errors:
            output_lines.append(f"  {e}")
        if not errors:
            output_lines.append("  (No errors detected)")
        output_lines.append("")
    # OCR screenshots
    for img in png_files:
        text = ocr_image(img)
        section = f"--- {os.path.basename(img)}: OCR text ---"
        output_lines.append(section)
        output_lines.append(text if text else "  (No text detected)")
        output_lines.append("")
    # Print and write summary log
    summary = '\n'.join(output_lines)
    print(summary)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')  # Fix AttributeError: use datetime.now()
    summary_path = os.path.join(shots_dir, f'diagnostics_summary_{ts}.log')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"\nDiagnostics summary saved to {summary_path}")

if __name__ == "__main__":
    main()
