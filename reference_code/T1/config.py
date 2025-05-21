"""
config.py - Centralized configuration for Zoom DNC Genie
"""

# URLs
GMAIL_INBOX = "https://mail.google.com/mail/u/0/#inbox"
ZOOM_SIGNIN_URL = "https://www.zoom.us/signin"
ZOOM_PROFILE_URL = "https://zoom.us/profile"
ZOOM_DASHBOARD_URL = "https://zoom.us/dashboard"
# Contact Center Admin Preferences (used for DNC operations)
ZOOM_CONTACT_CENTER_ADMIN_URL = "https://zoom.us/cci/index/admin#/admin-preferences"
# Updated to use the correct blocked-list URL for Workplace DNC operations
ZOOM_WORKPLACE_URL = "https://zoom.us/pbx/page/telephone/Settings#/settings/blocked-list?"
# ChromeDriver Download URL Template
CHROMEDRIVER_DOWNLOAD_URL_TEMPLATE = "https://storage.googleapis.com/chrome-for-testing-public/{version}/win{bitness}/chromedriver-win{bitness}.zip"


# Timeouts (seconds)
DEFAULT_WAIT = 20
LOGIN_WAIT = 30

# Selectors
EMAIL_INPUT_ID = "email"
PASSWORD_INPUT_ID = "password"
SIGN_IN_BTN_ID = "js_btn_login"
RECAPTCHA_ERROR_SELECTOR = "div.zm-message.zm-message--error"

# Error Texts
NETWORK_ERROR_TEXT = "Network Error"
RECAPTCHA_ERROR_TEXT = "An error with reCAPTCHA occured"

# Retry counts
MAX_LOGIN_RETRIES = 3

# Environment variable keys
ENV_EMAIL = "ZOOM_EMAIL"
ENV_PASSWORD = "ZOOM_PASSWORD"
