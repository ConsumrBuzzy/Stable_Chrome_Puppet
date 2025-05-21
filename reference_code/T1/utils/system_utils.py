"""
system_utils.py
System and architecture utility functions extracted from ZoomDNCGenie.py for modular use.
"""
import os
import struct
import subprocess
import platform
import re

from colorama import Fore, Style
import logging

def check_architecture():
    """Warn if Python and Chrome architectures do not match."""
    py_arch = struct.calcsize("P") * 8
    chrome_arch = "64-bit" if platform.machine().endswith('64') else "32-bit"
    if (py_arch == 32 and chrome_arch == "64-bit") or (py_arch == 64 and chrome_arch == "32-bit"):
        print(Fore.YELLOW + f"[WARNING] Python is {py_arch}-bit but your Chrome is {chrome_arch}. This can cause driver errors. Consider matching architectures." + Style.RESET_ALL)
        logging.warning(f"Python is {py_arch}-bit but Chrome is {chrome_arch}. Potential driver mismatch.")

def get_chrome_version():
    """Detect installed Chrome version via registry or command line."""
    version = None
    try:
        # Try registry (Windows)
        import winreg
        reg_path = r"SOFTWARE\\Google\\Chrome\\BLBeacon"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
        version, _ = winreg.QueryValueEx(key, "version")
        winreg.CloseKey(key)
    except Exception:
        # Try command line
        try:
            proc = subprocess.run([
                r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "--version"],
                capture_output=True, text=True)
            out = proc.stdout.strip() or proc.stderr.strip()
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)", out)
            if match:
                version = match.group(1)
        except Exception:
            pass
    return version

def get_chrome_bitness():
    """Detect Chrome bitness by inspecting the executable."""
    chrome_path = r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
    if not os.path.exists(chrome_path):
        return None
    with open(chrome_path, 'rb') as f:
        header = f.read(0x1000)
        if b'PE\x00\x00L\x01\x00\x00' in header:
            return '32'
        elif b'PE\x00\x00d\x86\x00\x00' in header or b'PE\x00\x00\x64\x86\x00\x00' in header:
            return '64'
    # Fallback: use directory
    return '64' if 'Program Files' in chrome_path else '32'

def get_python_bitness():
    """Return Python bitness as string ('32' or '64')."""
    return str(struct.calcsize("P") * 8)
