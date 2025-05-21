import os
from PIL import Image
import pytesseract
# Explicitly set the Tesseract executable path for Windows users
# Update this path if your installation is elsewhere
# Set the tesseract_cmd path to your Tesseract installation. Update if installed elsewhere.
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
import sys

"""
This script extracts text from all image files in the specified directory (default: current directory).
Requirements:
    - pip install pytesseract pillow
    - Tesseract OCR must be installed and on your PATH.
Usage:
    python extract_text_from_images.py [optional_image_dir]
Outputs:
    Prints extracted text for each image file.
"""

INPUT_PATH = sys.argv[1] if len(sys.argv) > 1 else "."
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tiff")

def extract_text_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text

def main():
    # If input is a file, process just that file
    if os.path.isfile(INPUT_PATH):
        print(f"\n--- Text from {os.path.basename(INPUT_PATH)} ---")
        text = extract_text_from_image(INPUT_PATH)
        print(text.strip())
    # If input is a directory, process all images in it
    elif os.path.isdir(INPUT_PATH):
        for filename in os.listdir(INPUT_PATH):
            if filename.lower().endswith(IMAGE_EXTS):
                print(f"\n--- Text from {filename} ---")
                text = extract_text_from_image(os.path.join(INPUT_PATH, filename))
                print(text.strip())
    else:
        print(f"Error: {INPUT_PATH} is not a valid file or directory.")

if __name__ == "__main__":
    main()