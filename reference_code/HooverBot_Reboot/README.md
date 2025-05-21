# HooverBot

A Python script to automate adding phone numbers to Telesero's blacklist and DNC (Do Not Call) lists across multiple servers.

## Features

- Adds phone numbers to both blacklist and DNC lists
- Supports multiple Telesero servers/campaigns
- Uses a clean Chrome instance for each server
- Automatic ChromeDriver management
- Comprehensive logging
- Error handling with screenshots
- System cleanup utilities

## Prerequisites

- Python 3.7+
- Google Chrome or Chromium browser
- Internet connection

## Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with your Telesero password:
   ```
   TELESERO_PASSWORD=your_password_here
   # Optional: Specify Chrome path if not in default location
   # CHROME_PATH=C:\\path\\to\\chrome.exe
   ```

## Usage

### Command Line

```
python main.py [phone_number]
```

If no phone number is provided, you'll be prompted to enter one.

### Options

- The script runs in non-headless mode by default. To run in headless mode, modify `main.py` and change `headless=False` to `headless=True` in the `ChromeManager` initialization.
- Screenshots are saved automatically when errors occur.
- Logs are saved to `hooverbot_YYYY-MM-DD_HH-MM-SS.log`.

## Configuration

Edit the `SERVERS` list in `main.py` to add/remove servers or modify campaign values.

## Troubleshooting

1. **Chrome not found**: 
   - Ensure Chrome is installed
   - Or set the `CHROME_PATH` in your `.env` file

2. **WebDriver issues**:
   - The script will automatically download the correct ChromeDriver version
   - If you encounter version mismatches, delete the `.wdm` folder in your home directory

3. **Connection issues**:
   - Check your internet connection
   - Verify the Telesero portal URLs are correct and accessible

## Logs

Logs are saved to timestamped files in the script's directory with the format `hooverbot_*.log`.

## License

This project is for educational purposes only. Use responsibly and in compliance with all applicable laws and terms of service.
