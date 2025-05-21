"""
TeleseroListBalancer - Automated Call Center List Management System
Following SOLID Principles:
- Single Responsibility: Each class has one job
- Open/Closed: Extensible without modification
- Liskov Substitution: Subtypes must be substitutable
- Interface Segregation: Specific interfaces
- Dependency Inversion: Depend on abstractions
"""

import sys
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('telesero_balancer.log')
    ]
)

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_USERNAME = "TOBOR"
DEFAULT_PASSWORD = "R0b0t!c47#"
PORTAL_URL = "https://portal.teleserosuite.com/contact-center/monitoring/"

# Server Type Designations
SERVER_TYPES = {
    '5': 'OSD',  # Server 5 is OSD type
    '6': 'GMB',  # Server 6 is GMB type
    '7': 'OSD',  # Server 7 is OSD type
    'A': 'GMB',  # Server A is GMB type
    '10': 'OSD', # Server I10 is OSD type
    '11': 'OSD'  # Server I11 is OSD type
}

# Server to Campaign ID mapping
SERVER_CAMPAIGN_MAP = {
    '5': '1600',  # OSD server
    '6': '220',   # GMB server (Fronter)
    '7': '580',   # OSD server
    'A': '920',   # GMB server (Fronter)
    '10': '990',  # OSD server I10
    '11': '710'   # OSD server I11
}

# Campaign types mapping for multi-campaign servers
CAMPAIGN_TYPES = {
    '6_FRONTER': '220',
    '6_CLOSER': '210',
    'A_FRONTER': '920',
    'A_CLOSER': '900'
}

# Multi-campaign server list
MULTI_CAMPAIGN_SERVERS = ['6', 'A']

# Server specific configurations
SERVER_CONFIG = {
    '5': {'type': 'OSD', 'is_multi': False, 'campaign': '1600'},
    '6': {'type': 'GMB', 'is_multi': True, 'campaigns': {'fronter': '220', 'closer': '210'}},
    'A': {'type': 'GMB', 'is_multi': True, 'campaigns': {'fronter': '920', 'closer': '900'}},
    '7': {'type': 'OSD', 'is_multi': False, 'campaign': '580'},
    '10': {'type': 'OSD', 'is_multi': False, 'campaign': '990'},
    '11': {'type': 'OSD', 'is_multi': False, 'campaign': '710'}
}

# Default agent prefixes
DEFAULT_AGENT_PREFIXES = {
    "6": {  # For IB6
        "FRONTERS": ["MEBS", "ABS"],
        "CLOSERS": ["BB", "NJ"]
    },
    "A": {  # For IBA
        "FRONTERS": ["MEBS", "ABS", "RC"],
        "CLOSERS": ["BB"]
    },
    # Campaign-specific prefixes
    "920": {  # IBA Fronter Campaign
        "FRONTERS": ["MEBS", "ABS", "RC"],
        "CLOSERS": []
    },
    "900": {  # IBA Closer Campaign
        "FRONTERS": [],
        "CLOSERS": ["BB"]
    },
    "220": {  # IB6 Fronter Campaign
        "FRONTERS": ["MEBS", "ABS"],
        "CLOSERS": []
    },
    "210": {  # IB6 Closer Campaign
        "FRONTERS": [],
        "CLOSERS": ["BB", "NJ"]
    },
    # Default values if not specified for a server
    "default": {
        "FRONTERS": [],
        "CLOSERS": []
    }
}

# Performance thresholds for GMB servers
GMB_THRESHOLDS = {
    'CONVERSION_RATE_THRESHOLD': 0.50,  # 50% conversion threshold
    'CONTACT_COUNT_THRESHOLD': 400,     # Check conversion after 400 contacts
    'CONTACT_RATE_THRESHOLD': 10.0,     # 10% contact rate threshold
    'CONTACT_RATE_COUNT': 80,           # Check contact rate after 80 contacts
    'REST_TIME': 60,                    # Check every 60 seconds
    'TOO_SOON_THRESHOLD': 60            # Minimum time between list checks
}

# Performance thresholds for OSD servers
OSD_THRESHOLDS = {
    'CONVERSION_RATE_THRESHOLD': 0.20,   # 30% conversion threshold
    'CONTACT_COUNT_THRESHOLD': 500,     # Check conversion after 300 contacts
    'CONTACT_RATE_THRESHOLD': 7.0,      # 7% contact rate threshold
    'CONTACT_RATE_COUNT': 100,           # Check contact rate after 80 contacts
    'REST_TIME': 60,                    # Check every 60 seconds
    'TOO_SOON_THRESHOLD': 60            # Minimum time between list checks
}

# Default to OSD thresholds
CONVERSION_RATE_THRESHOLD = OSD_THRESHOLDS['CONVERSION_RATE_THRESHOLD']
CONTACT_COUNT_THRESHOLD = OSD_THRESHOLDS['CONTACT_COUNT_THRESHOLD']
REST_TIME = OSD_THRESHOLDS['REST_TIME']
CONTACT_RATE_THRESHOLD = OSD_THRESHOLDS['CONTACT_RATE_THRESHOLD']
CONTACT_RATE_COUNT = OSD_THRESHOLDS['CONTACT_RATE_COUNT']
TOO_SOON_THRESHOLD = OSD_THRESHOLDS['TOO_SOON_THRESHOLD']

# Agent prefixes for server verification
AGENT_PREFIXES = DEFAULT_AGENT_PREFIXES

# Lists to ignore when making changes
IGNORE_LIST = []  # Add any list IDs that should be ignored

# Portal URL for web interface
PORTAL_URL = "https://telesero.com/portal/index.php"

# Default credentials
DEFAULT_USERNAME = "TOBOR"
DEFAULT_PASSWORD = "password"  # This should be changed or provided at runtime

# Log in with these credentials
logger.info("Configuration loaded successfully")

# Define performance thresholds
def load_credentials():
    """Load hard-coded credentials"""
    # Hard-coded values instead of loading from file
    stored_creds = {}
    portal_url = "https://portal.teleserosuite.com/contact-center/monitoring/"
    agent_prefixes = {
        "fronter": ["F", "FT"],
        "closer": ["C", "CT"]
    }
    return stored_creds, portal_url, agent_prefixes

def get_user_credentials(server_id: str) -> Dict[str, str]:
    """Return hard-coded credentials for the specified server"""
    # Hard-coded username and password
    default_username = "TOBOR"
    default_password = "R0b0t!c47#"
    
    # Handle both IB and I format servers
    server_prefix = "IB" if server_id in ["5", "6", "7", "A"] else "I"
    
    return {
        "username": f"{server_prefix}{server_id}\\{default_username}",
        "password": default_password
    }

def get_list_ids() -> List[str]:
    """Prompt user for list IDs"""
    print("\nEnter list IDs to balance (comma-separated) or press Enter to process all lists")
    list_input = input("List IDs: ").strip()
    if not list_input:
        return None
    return [lid.strip() for lid in list_input.split(",") if lid.strip()]

def get_server_config(server_id: str, creds: Dict[str, str], list_ids: List[str] = None, portal_url: Optional[str] = None) -> Dict:
    """Create server configuration with provided credentials"""
    # Updated server type determination - I10 and I11 are OSD servers
    server_type = ServerType.GMB if server_id in ["6", "A"] else ServerType.OSD
    
    if server_type == ServerType.OSD:
        campaign_ids = {"main": SERVER_CAMPAIGN_MAP[server_id]}
    else:
        # For GMB servers, use the corresponding campaign IDs from SERVER_CAMPAIGN_MAP
        campaign_ids = {
            "fronter": "920" if server_id == "A" else "220",  # IBA uses 920, IB6 uses 220
            "closer": "900" if server_id == "A" else "210"    # IBA uses 900, IB6 uses 210
        }
    
    return {
        "portal_url": portal_url or "https://portal.teleserosuite.com/contact-center/monitoring/",
        "thresholds": PerformanceThresholds(
            conversion_rate=GMB_THRESHOLDS['CONVERSION_RATE_THRESHOLD'] if server_type == ServerType.GMB else OSD_THRESHOLDS['CONVERSION_RATE_THRESHOLD'],
            contact_count=GMB_THRESHOLDS['CONTACT_COUNT_THRESHOLD'] if server_type == ServerType.GMB else OSD_THRESHOLDS['CONTACT_COUNT_THRESHOLD'],
            contact_rate=GMB_THRESHOLDS['CONTACT_RATE_THRESHOLD'],
            contact_rate_count=GMB_THRESHOLDS['CONTACT_RATE_COUNT'],
            rest_time=GMB_THRESHOLDS['REST_TIME']
        ),
        "server_configs": {
            server_id: ServerConfig(
                server_id=server_id,
                server_type=server_type,
                campaign_ids=campaign_ids,
                is_multi_campaign=server_type == ServerType.GMB,
                username=creds["username"],
                password=creds["password"],
                list_ids=list_ids
            )
        }
    }

class ServerType(Enum):
    """Server type enumeration"""
    OSD = "OSD"  # Outbound Single Dialer
    GMB = "GMB"  # Guided Manual Blending (includes both GMB and IBA servers)

@dataclass
class ServerConfig:
    """Server configuration data class"""
    server_id: str
    server_type: ServerType
    campaign_ids: Dict[str, str]
    is_multi_campaign: bool
    username: str = ""
    password: str = ""
    list_ids: List[str] = None  # Added list_ids field

@dataclass
class PerformanceThresholds:
    """Performance thresholds data class"""
    conversion_rate: float = 0.25  # 0.35%
    contact_count: int = 350  # Check conversion after 350 contacts
    contact_rate: float = 10.0  # 10% contact rate threshold
    contact_rate_count: int = 100  # Check contact rate after 80 contacts
    rest_time: int = 60  # 60 seconds between checks

    def __post_init__(self):
        """Validate threshold values"""
        if not 0 <= self.conversion_rate <= 100:
            raise ValueError("Conversion rate must be between 0 and 100")
        if self.contact_count < 0:
            raise ValueError("Contact count must be non-negative")
        if not 0 <= self.contact_rate <= 100:
            raise ValueError("Contact rate must be between 0 and 100")
        if self.contact_rate_count < 0:
            raise ValueError("Contact rate count must be non-negative")
        if self.rest_time < 0:
            raise ValueError("Rest time must be non-negative")
        
        # Store original percentage values for comparison
        # The conversion_rate is already in percentage form (e.g., 0.35 means 0.35%)
        self.conversion_rate_pct = self.conversion_rate  # Don't multiply by 100
        self.contact_rate_pct = self.contact_rate  # Keep contact rate as is (e.g., 10.0 means 10%)

class IListPerformanceAnalyzer(ABC):
    """Interface for list performance analysis"""
    @abstractmethod
    def analyze_performance(self, list_id: str, metrics: dict) -> bool:
        """Analyze list performance and return True if performing well"""
        pass

class IAgentVerifier(ABC):
    """Interface for agent verification"""
    @abstractmethod
    def verify_agents(self, driver: webdriver.Chrome, campaign_id: str, agent_type: str) -> bool:
        """Verify presence of required agents"""
        pass

class StandardPerformanceAnalyzer(IListPerformanceAnalyzer):
    """Standard implementation of list performance analysis"""
    def __init__(self, thresholds: PerformanceThresholds, server_type: ServerType):
        self.thresholds = thresholds
        self.server_type = server_type

    def analyze_performance(self, list_id: str, metrics: dict) -> bool:
        try:
            # Check for required metrics
            required_metrics = ['contact_count', 'conversion_rate', 'contact_rate', 'lead_count']
            if self.server_type == ServerType.OSD:
                required_metrics.extend(['sales_count'])
                
            if not all(key in metrics for key in required_metrics):
                logger.warning(f"Missing required metrics for list {list_id}")
                return True  # Conservative approach: don't swap if we don't have all metrics
            
            # For active lists, we need leads
            if metrics.get('is_active', False) and metrics['lead_count'] == 0:
                logger.info(f"List {list_id} is active but has no leads")
                return False
            
            # Check contact count threshold
            if metrics['contact_count'] < self.thresholds.contact_count:
                logger.info(f"List {list_id} has insufficient contact count: {metrics['contact_count']}")
                return True  # Not enough data to make decision
            
            # Check conversion rate threshold (using dashboard conversion for both OSD and GMB)
            if metrics['conversion_rate'] < self.thresholds.conversion_rate * 100:  # Convert threshold to percentage
                logger.info(f"List {list_id} has low conversion rate: {metrics['conversion_rate']:.2f}%")
                return False
            
            # Check contact rate threshold
            if (metrics['contact_rate'] < self.thresholds.contact_rate * 100 and  # Convert threshold to percentage
                metrics['contact_count'] >= self.thresholds.contact_rate_count):
                logger.info(f"List {list_id} has low contact rate: {metrics['contact_rate']:.2f}%")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error analyzing performance for list {list_id}: {e}")
            return True  # Conservative approach: don't swap on error

class AgentVerifier(IAgentVerifier):
    """Implementation of agent verification"""
    def __init__(self, agent_prefixes: Dict[str, List[str]], min_agents: Dict[str, int] = None):
        logger.info("Initializing AgentVerifier with prefixes: %s", agent_prefixes)
        self.agent_prefixes = agent_prefixes
        self.min_agents = min_agents or {
            "FRONTERS": 2,  # Default minimum fronter agents
            "CLOSERS": 1,   # Default minimum closer agents
            "ANY": 1        # Default minimum for OSD servers
        }
        logger.info("Minimum agents required: %s", self.min_agents)

    def verify_agents(self, driver: webdriver.Chrome, campaign_id: str, agent_type: str) -> bool:
        """Verify presence of required agents"""
        try:
            is_osd = agent_type == "ANY"
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Wait for the table to be present
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "online-agents-table"))
                        )
                        time.sleep(2)  # Additional wait after finding table
                    except TimeoutException:
                        logger.error(f"Agent table not found in campaign")
                        logger.info("Waiting 60 seconds before retry...")
                        time.sleep(60)
                        return False

                    # First check for "no online agents" message
                    try:
                        no_agents_msg = driver.find_element(By.XPATH, "//div[contains(@class, 'alert-info')]//strong[contains(text(), 'Information!')]")
                        if no_agents_msg:
                            logger.info("No online agents message found in table")
                            logger.info("Waiting 60 seconds before retry...")
                            time.sleep(60)
                            return False
                    except NoSuchElementException:
                        # No message found, continue checking for agents
                        pass

                    # Get fresh copy of the table HTML to avoid stale elements
                    table_html = driver.find_element(By.ID, "online-agents-table").get_attribute('outerHTML')
                    soup = BeautifulSoup(table_html, 'html.parser')
                    
                    # Find all agent rows using BeautifulSoup
                    agent_rows = soup.select("tbody tr:first-child td:first-child")
                    
                    if not agent_rows:
                        logger.info("No agents found in the table")
                        logger.info("Waiting 60 seconds before retry...")
                        time.sleep(60)
                        return False
                    
                    if is_osd:
                        # For OSD servers, check minimum agent count
                        agent_count = len(agent_rows)
                        min_required = self.min_agents["ANY"]
                        logger.info(f"Found {agent_count} agents in OSD campaign (minimum {min_required} required)")
                        if agent_count < min_required:
                            logger.info("Insufficient agents found")
                            logger.info("Waiting 60 seconds before retry...")
                            time.sleep(60)
                        return agent_count >= min_required
                    
                    # For GMB/IBA servers, check for specific agent types
                    # First try server-level prefixes
                    logger.info(f"Checking prefixes for campaign {campaign_id}, agent type {agent_type}")
                    logger.info(f"Available prefixes in config: {self.agent_prefixes}")
                    
                    server_id = "A" if campaign_id in ["920", "900"] else "6"
                    valid_prefixes = []
                    
                    if server_id in self.agent_prefixes:
                        valid_prefixes = self.agent_prefixes[server_id].get(agent_type, [])
                        logger.info(f"Using server-level prefixes for {server_id}: {valid_prefixes}")
                    
                    # If no server prefixes, try campaign-specific prefixes
                    if not valid_prefixes and campaign_id in self.agent_prefixes:
                        valid_prefixes = self.agent_prefixes[campaign_id].get(agent_type, [])
                        logger.info(f"Using campaign-specific prefixes: {valid_prefixes}")
                    
                    if not valid_prefixes:
                        logger.warning(f"No valid prefixes found for {agent_type} in server {server_id} or campaign {campaign_id}")
                        return False
                    
                    valid_agent_count = 0
                    agent_names = []
                    
                    for row in agent_rows:
                        try:
                            agent_name = row.text.strip()
                            agent_names.append(agent_name)
                            if any(agent_name.startswith(prefix) for prefix in valid_prefixes):
                                valid_agent_count += 1
                                logger.info(f"Found valid {agent_type} agent: {agent_name}")
                        except Exception as e:
                            logger.error(f"Error processing agent row: {e}")
                            continue
                    
                    min_required = self.min_agents.get(agent_type, 1)
                    logger.info(f"Found {valid_agent_count} valid {agent_type} agents (minimum {min_required} required)")
                    if agent_names:
                        logger.info(f"All agent names found: {agent_names}")
                    
                    if valid_agent_count < min_required:
                        logger.info("Insufficient valid agents found")
                        logger.info("Waiting 60 seconds before retry...")
                        time.sleep(60)
                    
                    return valid_agent_count >= min_required
                    
                except Exception as e:
                    logger.error(f"Error during agent verification (attempt {retry_count + 1}/{max_retries}): {e}")
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.info("Retrying agent verification...")
                        time.sleep(2)  # Short wait between retries
                    else:
                        logger.error("Max retries reached for agent verification")
                        return False
            
            return False  # Return False if all retries failed
            
        except Exception as e:
            logger.error(f"Error verifying agents for campaign {campaign_id}: {e}")
            logger.error("Stack trace:", exc_info=True)
            return False

    def get_agent_count(self, driver: webdriver.Chrome, campaign_id: str, agent_type: str) -> int:
        """Get the count of valid agents for a specific type"""
        try:
            # Wait for the table to be present
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "online-agents-table"))
                )
                time.sleep(2)
            except TimeoutException:
                logger.error(f"Agent table not found in campaign")
                return 0

            # Find all agent rows
            agent_rows = driver.find_elements(By.XPATH, "//tbody/tr[1]/td[1][contains(text(), ' ')]")
            
            if not agent_rows:
                return 0
            
            if agent_type == "ANY":
                return len(agent_rows)
            
            # For specific agent types, check prefixes
            if campaign_id not in self.agent_prefixes:
                return 0
            
            valid_prefixes = self.agent_prefixes.get(campaign_id, {}).get(agent_type, [])
            valid_count = 0
            
            for row in agent_rows:
                try:
                    agent_name = row.text.strip()
                    if any(agent_name.startswith(prefix) for prefix in valid_prefixes):
                        valid_count += 1
                except Exception:
                    continue
            
            return valid_count
            
        except Exception as e:
            logger.error(f"Error getting agent count for campaign {campaign_id}: {e}")
            return 0

    def get_agent_names(self, driver: webdriver.Chrome, campaign_id: str, agent_type: str) -> List[str]:
        """Get the names of all valid agents for a specific type"""
        try:
            # Wait for the table to be present
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "online-agents-table"))
                )
                time.sleep(2)
            except TimeoutException:
                logger.error(f"Agent table not found in campaign")
                return []

            # Find all agent rows
            agent_rows = driver.find_elements(By.XPATH, "//tbody/tr[1]/td[1][contains(text(), ' ')]")
            
            if not agent_rows:
                return []
            
            if agent_type == "ANY":
                return [row.text.strip() for row in agent_rows]
            
            # For specific agent types, check prefixes
            if campaign_id not in self.agent_prefixes:
                return []
            
            valid_prefixes = self.agent_prefixes.get(campaign_id, {}).get(agent_type, [])
            valid_agents = []
            
            for row in agent_rows:
                try:
                    agent_name = row.text.strip()
                    if any(agent_name.startswith(prefix) for prefix in valid_prefixes):
                        valid_agents.append(agent_name)
                except Exception:
                    continue
            
            return valid_agents
            
        except Exception as e:
            logger.error(f"Error getting agent names for campaign {campaign_id}: {e}")
            return []

    def update_min_agents(self, new_minimums: Dict[str, int]) -> None:
        """Update minimum agent requirements"""
        self.min_agents.update(new_minimums)
        logger.info(f"Updated minimum agent requirements: {self.min_agents}")

class WebPortalInterface:
    """Handles all web portal interactions"""
    def __init__(self, url: str):
        self.url = url
        self.driver = None
        self.setup_driver()
        self.dashboard_html = None

    def setup_driver(self):
        """Initialize WebDriver with appropriate settings"""
        try:
            options = webdriver.ChromeOptions()
            # Always run in visible mode for now
            options.add_argument('--start-maximized')
            options.add_argument('--disable-dev-shm-usage')
            
            service = webdriver.chrome.service.Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(10)  # Set implicit wait
            logger.info("WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def login(self, username: str, password: str):
        """Handle portal login"""
        try:
            logger.info("Attempting to log in...")
            self.driver.get(self.url)
            
            # Wait for login form to be present
            wait = WebDriverWait(self.driver, 10)
            username_field = wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = wait.until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            
            # Clear fields and enter credentials
            username_field.clear()
            password_field.clear()
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            # Find and click login button
            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            login_button.click()
            
            # Wait for successful login (monitoring page to load)
            wait.until(
                EC.url_to_be("https://portal.teleserosuite.com/contact-center/monitoring/")
            )
            
            logger.info("Successfully logged into portal")
            return True
        except TimeoutException as e:
            logger.error("Timeout while logging in - page or elements not loaded")
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    def select_campaign(self, campaign_id: str) -> bool:
        """Selects the campaign from the Live Dashboard using JavaScript."""
        try:
            logger.info(f"Selecting campaign {campaign_id}...")
            # Wait for the page to fully load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Execute JavaScript to select the campaign
            script = """
            function selectCampaign(campaignId) {
                var select = document.querySelector('select.select2-hidden-accessible');
                if (select) {
                    select.value = campaignId;
                    var event = new Event('change', { bubbles: true });
                    select.dispatchEvent(event);
                    return true;
                }
                return false;
            }
            return selectCampaign(arguments[0]);
            """
            
            result = self.driver.execute_script(script, campaign_id)
            if result:
                logger.info(f"Campaign {campaign_id} selected successfully")
                time.sleep(2)  # Wait for selection to take effect
                return True
            else:
                logger.error("Campaign selector not found")
                return False
                
        except Exception as e:
            logger.error(f"Error selecting campaign: {e}")
            return False

    def save_dashboard_html(self):
        """Save the dashboard HTML content."""
        try:
            # Wait for the table to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table"))
            )
            
            # Get the HTML content
            self.dashboard_html = self.driver.page_source
            logger.info("Dashboard HTML saved")
            
        except Exception as e:
            logger.error(f"Error saving dashboard HTML: {e}")
            logger.error("Stack trace:", exc_info=True)
            self.dashboard_html = None

    def parse_dashboard_html(self) -> dict:
        """Parses the dashboard HTML to extract list data."""
        try:
            logger.info("Parsing dashboard HTML...")
            soup = BeautifulSoup(self.dashboard_html, "html.parser")
            list_data = {}

            # Find the list performance table
            table_div = soup.find('div', {'id': 'list-performance-table'})
            if not table_div:
                logger.error("List performance table div not found")
                return {}
                
            table = table_div.find('table')
            if not table:
                logger.error("List table not found in dashboard")
                return {}

            rows = table.select("tbody tr")
            for row in rows:
                try:
                    # Get list ID from the link
                    list_id_element = row.select_one("td a")
                    if list_id_element is None:
                        continue
                    
                    list_id = list_id_element.text.strip().split()[0]
                    
                    # Get all stats
                    cells = row.select("td")
                    if len(cells) < 8:  # Need all columns
                        continue
                    
                    # Extract data
                    is_active = "bg-active" in row.get("class", [])
                    
                    # Get lead count for all lists (column 2)
                    lead_count_text = cells[1].text.strip()  # Dialable Leads column
                    try:
                        lead_count = int(lead_count_text.replace(',', '')) if lead_count_text != 'N/A' else 0
                    except (ValueError, TypeError):
                        lead_count = 0
                    
                    # Contact rate (column 3)
                    contact_rate_text = cells[2].text.strip().replace('%', '').strip()
                    contact_rate = float(contact_rate_text) if contact_rate_text and contact_rate_text != 'N/A' else 0.0
                    
                    # Contacts (column 4)
                    contact_text = cells[3].text.strip().replace(',', '')
                    try:
                        contact_count = int(contact_text) if contact_text and contact_text != 'N/A' else 0
                    except (ValueError, TypeError):
                        contact_count = 0
                    
                    # Sales/Appointments (column 6)
                    sales_text = cells[5].text.strip().replace(',', '')
                    try:
                        sales_count = int(sales_text) if sales_text and sales_text != 'N/A' else 0
                    except (ValueError, TypeError):
                        sales_count = 0
                    
                    # Conversion rate (column 8)
                    conversion_text = cells[7].text.strip().replace('%', '').strip()
                    conversion_rate = float(conversion_text) if conversion_text and conversion_text != 'N/A' else 0.0
                    
                    # Calculate appointment rate for OSD
                    appt_rate = (sales_count / contact_count * 100) if contact_count > 0 else 0.0
                    
                    list_data[list_id] = {
                        'contact_count': contact_count,
                        'contact_rate': contact_rate,
                        'conversion_rate': conversion_rate,
                        'is_active': is_active,
                        'has_leads': lead_count > 0,
                        'lead_count': lead_count,
                        'sales_count': sales_count,
                        'appointment_rate': appt_rate,
                        'timestamp': time.time()
                    }
                    
                    logger.info(f"\nList {list_id}:")
                    logger.info(f"  Status: {'Active' if is_active else 'Inactive'}")
                    logger.info(f"  Has Leads: {lead_count > 0}")
                    logger.info(f"  Lead Count: {lead_count}")
                    logger.info(f"  Contacts: {contact_count}")
                    logger.info(f"  Contact Rate: {contact_rate:.2f}%")
                    logger.info(f"  Sales/Appointments: {sales_count}")
                    logger.info(f"  Appointment Rate: {appt_rate:.2f}%")
                    logger.info(f"  Conversion Rate: {conversion_rate:.2f}%")
                    
                except Exception as e:
                    logger.error(f"Error parsing row: {e}")
                    continue

            logger.info(f"Successfully parsed {len(list_data)} lists")
            
            # Log active and inactive lists
            active_lists = [lid for lid, m in list_data.items() if m['is_active']]
            inactive_lists = [lid for lid, m in list_data.items() if not m['is_active']]
            logger.info(f"Active lists: {active_lists}")
            logger.info(f"Inactive lists: {inactive_lists}")
            
            return list_data
            
        except Exception as e:
            logger.error(f"Error parsing dashboard HTML: {e}")
            logger.error("Stack trace:", exc_info=True)
            return {}

    def get_campaign_metrics(self, campaign_id: str, metrics_history: dict = None) -> Dict[str, Dict]:
        """Get metrics for all lists in a campaign"""
        try:
            # Only select campaign if we're not already on it
            current_campaign = self.driver.execute_script("""
                var select = document.querySelector('select.select2-hidden-accessible');
                return select ? select.value : null;
            """)
            
            if current_campaign != campaign_id:
                if not self.select_campaign(campaign_id):
                    return {}
                # Wait for initial load after campaign change
                time.sleep(5)
            
            # Wait for the list performance table to be present and visible
            try:
                table_div = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "list-performance-table"))
                )
                # Additional wait for table body
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@id='list-performance-table']//tbody"))
                )
                time.sleep(2)  # Extra wait for data to populate
            except TimeoutException:
                logger.error("Timeout waiting for list performance table")
                logger.info("Waiting 60 seconds before retry...")
                time.sleep(60)
                return {}
            
            # Get the current page HTML
            self.dashboard_html = self.driver.page_source
            logger.info("Retrieved current dashboard HTML")
            
            logger.info("Parsing dashboard HTML...")
            soup = BeautifulSoup(self.dashboard_html, 'html.parser')
            metrics = {}
            
            # Find the list performance table specifically
            table_div = soup.find('div', {'id': 'list-performance-table'})
            if not table_div:
                logger.error("List performance table div not found")
                logger.info("Waiting 60 seconds before retry...")
                time.sleep(60)
                return {}
                
            table = table_div.find('table')
            if not table:
                logger.error("List table not found in dashboard")
                logger.info("Waiting 60 seconds before retry...")
                time.sleep(60)
                return {}
            
            # Get all rows from tbody
            tbody = table.find('tbody')
            if not tbody:
                logger.error("Table body not found")
                logger.info("Waiting 60 seconds before retry...")
                time.sleep(60)
                return {}
            
            # Check for empty table (no rows)
            rows = tbody.find_all('tr')
            if not rows:
                logger.info("List performance table is empty")
                logger.info("Waiting 60 seconds before retry...")
                time.sleep(60)
                return {}
                
            parsed_count = 0
            
            for row in rows:
                try:
                    # Get list ID from first column (it's in a link)
                    list_id_elem = row.find('a')
                    if not list_id_elem:
                        continue
                        
                    list_id = list_id_elem.get_text(strip=True).split()[0]
                    if not list_id.isdigit():
                        continue
                    
                    # Check if list is active based on row class
                    is_active = 'bg-active' in row.get('class', [])
                    
                    # Get all cells
                    cells = row.find_all('td')
                    if len(cells) < 8:  # Need all columns
                        continue
                    
                    try:
                        # Dialable leads (column 2)
                        lead_count_text = cells[1].get_text(strip=True).replace(',', '')
                        if lead_count_text == 'N/A':
                            # Try to get previous value from history
                            if metrics_history and list_id in metrics_history:
                                previous_metrics = metrics_history[list_id].get('dashboard_metrics', [])
                                if previous_metrics:
                                    lead_count = previous_metrics[-1].get('lead_count', 0)
                                    has_leads = previous_metrics[-1].get('has_leads', False)
                                    logger.info(f"Using previous lead count for list {list_id}: {lead_count}")
                                else:
                                    lead_count = 0
                                    has_leads = False
                                    logger.info(f"No previous metrics for list {list_id}, setting lead count to 0")
                            else:
                                lead_count = 0
                                has_leads = False
                                logger.info(f"No metrics history for list {list_id}, setting lead count to 0")
                        else:
                            lead_count = int(lead_count_text) if lead_count_text.isdigit() else 0
                            has_leads = lead_count > 0
                        
                        # Contact rate (column 3)
                        contact_rate_text = cells[2].get_text(strip=True).replace('%', '').strip()
                        contact_rate = float(contact_rate_text) if contact_rate_text and contact_rate_text != 'N/A' else 0.0
                        
                        # Contacts (column 4)
                        contact_text = cells[3].get_text(strip=True).replace(',', '')
                        contact_count = int(contact_text) if contact_text.isdigit() else 0
                        
                        # Sales/Appointments (column 6)
                        sales_text = cells[5].get_text(strip=True).replace(',', '')
                        sales_count = int(sales_text) if sales_text.isdigit() else 0
                        
                        # Conversion rate (column 8)
                        conversion_text = cells[7].get_text(strip=True).replace('%', '').strip()
                        conversion_rate = float(conversion_text) if conversion_text and conversion_text != 'N/A' else 0.0
                        
                        metrics[list_id] = {
                            'contact_count': contact_count,
                            'contact_rate': contact_rate,
                            'conversion_rate': conversion_rate,
                            'is_active': is_active,
                            'has_leads': has_leads,
                            'lead_count': lead_count,
                            'sales_count': sales_count,
                            'timestamp': time.time(),
                            'dialables_unavailable': lead_count_text == 'N/A'  # Track if dialables were N/A
                        }
                        parsed_count += 1
                        
                        logger.debug(f"List {list_id}: active={is_active}, leads={lead_count}, contacts={contact_count}, rate={contact_rate}%, conv={conversion_rate}%")
                        
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Error parsing metrics for list {list_id}: {e}")
                        continue
                    
                except Exception as e:
                    logger.error(f"Error parsing row: {e}")
                    continue
            
            logger.info(f"Successfully parsed {parsed_count} lists")
            
            # Log active and inactive lists
            active_lists = [lid for lid, m in metrics.items() if m['is_active']]
            inactive_lists = [lid for lid, m in metrics.items() if not m['is_active']]
            logger.info(f"Active lists: {active_lists}")
            logger.info(f"Inactive lists: {inactive_lists}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting campaign metrics: {e}")
            logger.error("Stack trace:", exc_info=True)
            return {}

    def __del__(self):
        """Cleanup method to ensure WebDriver is closed"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")

    def change_list(self, remove_list_id: str, new_list_id: str, campaign_id: str) -> bool:
        """Change a list in the campaign"""
        try:
            logging.info(f"Attempting to change list {remove_list_id} to {new_list_id} in campaign {campaign_id}")
            
            # Navigate to dialing strategy page with correct campaign ID
            list_url = f"https://portal.teleserosuite.com/dialing/strategy/manage/{campaign_id}"
            self.driver.get(list_url)
            time.sleep(5)  # Wait for page load
            
            # Verify the old list is present before attempting removal
            try:
                old_list_present = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//tr[td/input[@value='{remove_list_id}']]"))
                )
                if not old_list_present:
                    logger.error(f"Old list {remove_list_id} not found in dialing strategy")
                    return False
            except TimeoutException:
                logger.error(f"Old list {remove_list_id} not found in dialing strategy")
                return False
            
            # Find the percentage value of the list to be removed
            percentage_xpath = f"//tr[td/input[@value='{remove_list_id}']]//input[contains(@name, 'percent')]"
            percentage_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, percentage_xpath))
            )
            percentage_value = percentage_element.get_dom_attribute("value")
            
            # Remove the list
            remove_button_xpath = f"//tr[td/input[@value='{remove_list_id}']]//button[@class='btn btn-xs btn-icon btn-danger del']"
            remove_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, remove_button_xpath))
            )
            remove_button.click()
            time.sleep(2)
            
            # Verify the old list was removed
            try:
                old_list_removed = WebDriverWait(self.driver, 10).until_not(
                    EC.presence_of_element_located((By.XPATH, f"//tr[td/input[@value='{remove_list_id}']]"))
                )
                if not old_list_removed:
                    logger.error(f"Failed to remove old list {remove_list_id}")
                    return False
            except TimeoutException:
                pass  # List was removed successfully
            
            # Add the new list with correct campaign ID
            self.driver.execute_script(
                f"""
                var selectElement = document.querySelector("select[data-campaign-id='{campaign_id}']");
                if (selectElement) {{
                    var newOption = new Option("{new_list_id}", "{new_list_id}", true, true);
                    selectElement.appendChild(newOption);
                    $(selectElement).val("{new_list_id}").trigger('change');
                }}
                """
            )
            time.sleep(2)
            
            # Verify the new list was added
            try:
                new_list_present = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//tr[td/input[@value='{new_list_id}']]"))
                )
                if not new_list_present:
                    logger.error(f"Failed to add new list {new_list_id}")
                    return False
            except TimeoutException:
                logger.error(f"Failed to add new list {new_list_id}")
                return False
            
            # Set the percentage value for the new list
            self.driver.execute_script(
                f"""
                var rows = document.querySelectorAll("tr.lead-list-item");
                rows.forEach(function(row) {{
                    var listIdInput = row.querySelector("input[name*='[listId]']");
                    if (listIdInput && listIdInput.value == "{new_list_id}") {{
                        var percentageInput = row.querySelector("input[name*='[percent]']");
                        if (percentageInput) {{
                            percentageInput.value = "{percentage_value}";
                        }}
                    }}
                }});
                """
            )
            time.sleep(2)
            
            # Save the changes
            save_button_xpath = "//button[@type='submit' and contains(@class, 'btn-success')]"
            save_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, save_button_xpath))
            )
            save_button.click()
            time.sleep(5)  # Wait for save to complete
            
            # Verify the change in dialing strategy
            strategy_metrics = self.get_dialing_strategy_metrics(campaign_id)
            if not strategy_metrics:
                logger.error("Failed to verify list change - could not get strategy metrics")
                return False
            
            # Check if new list is present and old list is removed
            new_list_present = new_list_id in strategy_metrics
            old_list_removed = remove_list_id not in strategy_metrics
            
            if new_list_present and old_list_removed:
                logger.info("List change verified in dialing strategy")
                # Return to dashboard and reselect campaign
                logger.info("Returning to dashboard...")
                self.driver.get(self.url)
                time.sleep(5)
                
                if self.select_campaign(campaign_id):
                    logger.info(f"Successfully returned to dashboard and selected campaign {campaign_id}")
                    return True
                else:
                    logger.error("Failed to select campaign after successful list change")
                    return True  # Still return True as the list change was successful
            
            logger.error("Failed to verify list change in dialing strategy")
            return False
            
        except Exception as e:
            logger.error(f"List change failed: {e}")
            logger.error("Stack trace:", exc_info=True)
            return False

    def verify_list_performance(self, list_id: str, campaign_id: str, metrics_history: dict = None, thresholds = None) -> bool:
        """Verify a list's current performance before using it"""
        try:
            logger.info(f"Verifying performance for list {list_id}...")
            
            # For GMB campaigns, we need metrics from both campaigns
            if campaign_id in ["920", "220"]:  # Fronter campaigns
                fronter_metrics = self.get_campaign_metrics(campaign_id, metrics_history)
                closer_metrics = self.get_campaign_metrics(
                    "900" if campaign_id == "920" else "210",  # Get corresponding closer campaign
                    metrics_history
                )
                
                if not fronter_metrics or not closer_metrics:
                    logger.error("Failed to get metrics from both campaigns")
                    return False
                
                # Get metrics from both campaigns
                fronter_stats = fronter_metrics.get(list_id, {})
                closer_stats = closer_metrics.get(list_id, {})
                
                # Calculate combined metrics
                fronter_contacts = fronter_stats.get('contact_count', 0)
                closer_contacts = closer_stats.get('contact_count', 0)  # These are transfers
                contact_rate = fronter_stats.get('contact_rate', 0.0)
                is_active = fronter_stats.get('is_active', False) or closer_stats.get('is_active', False)
                has_leads = fronter_stats.get('has_leads', False)
                
                # Calculate transfer rate (conversion) only if we have fronter contacts
                transfer_rate = (closer_contacts / fronter_contacts * 100) if fronter_contacts > 0 else 0.0
                
                logger.info(f"List {list_id} combined metrics:")
                logger.info(f"  Active: {is_active}")
                logger.info(f"  Has Leads: {has_leads}")
                logger.info(f"  Fronter Contacts: {fronter_contacts}")
                logger.info(f"  Closer Transfers: {closer_contacts}")
                logger.info(f"  Transfer Rate: {transfer_rate:.2f}%")
                logger.info(f"  Contact Rate: {contact_rate:.2f}%")
                
                # For active lists, we need leads
                if is_active and not has_leads:
                    logger.info(f"List {list_id} is active but has no leads - not suitable")
                    return False
                
                # Always check transfer rate first if we have enough contacts
                if fronter_contacts >= thresholds.contact_count:
                    if transfer_rate >= thresholds.conversion_rate:
                        logger.info(f"List {list_id} has good transfer rate ({transfer_rate:.2f}% >= {thresholds.conversion_rate:.2f}%) - OK to use")
                        return True
                    else:
                        logger.info(f"List {list_id} has poor transfer rate ({transfer_rate:.2f}% < {thresholds.conversion_rate:.2f}%) with {fronter_contacts} contacts")
                        return False
                
                # If not enough contacts for transfer rate evaluation, check contact rate
                if fronter_contacts >= thresholds.contact_rate_count:
                    if contact_rate >= thresholds.contact_rate_pct:
                        logger.info(f"List {list_id} has good contact rate ({contact_rate:.2f}% >= {thresholds.contact_rate_pct:.2f}%) but needs more contacts for transfer rate evaluation - OK to try")
                        return True
                
                # If list is inactive and hasn't failed any checks, it's OK to try
                if not is_active:
                    logger.info(f"List {list_id} is inactive and hasn't proven poor performance - OK to try")
                    return True
            
            else:  # OSD campaign logic remains unchanged
                metrics = self.get_campaign_metrics(campaign_id, metrics_history)
                if not metrics or list_id not in metrics:
                    logger.info(f"List {list_id} not found in metrics - OK to try")
                    return True
                
                list_metrics = metrics[list_id]
                contacts = list_metrics.get('contact_count', 0)
                conversion = list_metrics.get('conversion_rate', 0)
                contact_rate = list_metrics.get('contact_rate', 0)
                is_active = list_metrics.get('is_active', False)
                has_leads = list_metrics.get('has_leads', False)
                
                # For active lists, we need leads
                if is_active and not has_leads:
                    logger.info(f"List {list_id} is active but has no leads - not suitable")
                    return False
                
                # Always check conversion rate first if we have enough contacts
                if contacts >= thresholds.contact_count:
                    if conversion >= thresholds.conversion_rate:
                        logger.info(f"List {list_id} has good conversion rate ({conversion:.2f}% >= {thresholds.conversion_rate:.2f}%) - OK to use")
                        return True
                    else:
                        logger.info(f"List {list_id} has poor conversion rate ({conversion:.2f}% < {thresholds.conversion_rate:.2f}%) with {contacts} contacts")
                        return False
                
                # If not enough contacts for conversion evaluation, check contact rate
                if contacts >= thresholds.contact_rate_count:
                    if contact_rate >= thresholds.contact_rate_pct:
                        logger.info(f"List {list_id} has good contact rate ({contact_rate:.2f}% >= {thresholds.contact_rate_pct:.2f}%) but needs more contacts for conversion evaluation - OK to try")
                        return True
                
                # If list is inactive and hasn't failed any checks, it's OK to try
                if not is_active:
                    logger.info(f"List {list_id} is inactive and hasn't proven poor performance - OK to try")
                    return True
            
            return True  # If we haven't found a reason to reject it, give it a try
            
        except Exception as e:
            logger.error(f"Error verifying list {list_id}: {e}")
            return False

    def get_dialing_strategy_metrics(self, campaign_id: str) -> Dict[str, Dict]:
        """Get metrics from the Dialing Strategy page for active lists"""
        try:
            logger.info(f"Getting dialing strategy metrics for campaign {campaign_id}")
            
            # Navigate to dialing strategy page
            list_url = f"https://portal.teleserosuite.com/dialing/strategy/manage/{campaign_id}"
            self.driver.get(list_url)
            time.sleep(5)  # Wait for page load
            
            # Get the page HTML
            strategy_html = self.driver.page_source
            soup = BeautifulSoup(strategy_html, 'html.parser')
            metrics = {}
            
            # Get current date for reset comparison
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Get mix name and method
            mix_name = soup.select_one("input.list-mix-name").get('value', '') if soup.select_one("input.list-mix-name") else ''
            mix_method = soup.select_one("select.list-mix-mixing-method option[selected]").get('value', '') if soup.select_one("select.list-mix-mixing-method option[selected]") else ''
            
            logger.info(f"Mix Name: {mix_name}")
            logger.info(f"Mix Method: {mix_method}")
            
            # Find all list rows
            rows = soup.select("tr.lead-list-item")
            for row in rows:
                try:
                    # Get list ID and name from hidden fields
                    list_id_input = row.select_one("input.lead-list-id")
                    list_name_input = row.select_one("input.lead-list-name")
                    dialable_input = row.select_one("input.lead-list-dialable-lead-count")
                    resets_input = row.select_one("input.lead-list-reset-times")
                    reset_time_input = row.select_one("input.lead-list-reset-time")
                    percent_input = row.select_one("input.lead-list-dialing-percentage")
                    priority_input = row.select_one("input[name*='priority']")
                    
                    if not list_id_input:
                        continue
                        
                    list_id = list_id_input.get('value', '').strip()
                    if not list_id:
                        continue
                    
                    # Extract metrics from hidden fields
                    list_name = list_name_input.get('value', '') if list_name_input else ''
                    dialables = int(dialable_input.get('value', '0')) if dialable_input else 0
                    resets = int(resets_input.get('value', '0')) if resets_input else 0
                    reset_time = reset_time_input.get('value', '') if reset_time_input else ''
                    percent = float(percent_input.get('value', '0')) if percent_input else 0.0
                    priority = int(priority_input.get('value', '0')) if priority_input else 0
                    
                    # Check if list was reset today
                    reset_today = False
                    if reset_time:
                        try:
                            reset_date = datetime.strptime(reset_time, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                            reset_today = reset_date == current_date
                        except ValueError:
                            logger.warning(f"Could not parse reset time for list {list_id}: {reset_time}")
                    
                    metrics[list_id] = {
                        'list_name': list_name,
                        'percent_blend': percent,
                        'dialables': dialables,
                        'resets': resets,
                        'last_reset': reset_time,
                        'reset_today': reset_today,
                        'priority': priority,
                        'is_active': True,  # If it's on this page, it's active
                        'mix_name': mix_name,
                        'mix_method': mix_method
                    }
                    
                    logger.info(f"\nList {list_id} ({list_name}) strategy metrics:")
                    logger.info(f"  Priority: {priority}")
                    logger.info(f"  Percent Blend: {percent:.1f}%")
                    logger.info(f"  Dialables: {dialables}")
                    logger.info(f"  Resets: {resets}")
                    logger.info(f"  Last Reset: {reset_time}")
                    logger.info(f"  Reset Today: {'Yes' if reset_today else 'No'}")
                    
                except Exception as e:
                    logger.error(f"Error processing strategy row: {e}")
                    continue
            
            logger.info(f"Successfully parsed strategy metrics for {len(metrics)} lists")
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting dialing strategy metrics: {e}")
            logger.error("Stack trace:", exc_info=True)
            return {}

@dataclass
class ListMetrics:
    """Data class for list performance metrics"""
    timestamp: str
    conversion_rate: float
    contact_count: int
    contact_rate: float
    is_active: bool

class ListPerformanceTracker:
    """Tracks list performance over time"""
    def __init__(self):
        self.performance_history: Dict[str, List[ListMetrics]] = {}

    def add_metrics(self, list_id: str, metrics: ListMetrics):
        """Add new metrics for a list"""
        if list_id not in self.performance_history:
            self.performance_history[list_id] = []
        self.performance_history[list_id].append(metrics)

    def get_metrics(self, list_id: str) -> List[ListMetrics]:
        """Get all metrics for a list"""
        return self.performance_history.get(list_id, [])

    def get_latest_metrics(self, list_id: str) -> Optional[ListMetrics]:
        """Get the most recent metrics for a list"""
        metrics = self.performance_history.get(list_id, [])
        return metrics[-1] if metrics else None

class ListManager:
    """Manages list performance tracking and changes"""

    def __init__(
        self,
        performance_analyzer: IListPerformanceAnalyzer,
        agent_verifier: IAgentVerifier,
        thresholds: PerformanceThresholds,
        list_ids: List[str] = None
    ):
        self.performance_analyzer = performance_analyzer
        self.agent_verifier = agent_verifier
        self.thresholds = thresholds
        self.list_ids = list_ids or []
        self.used_list_ids = set()
        self.failed_list_ids = set()
        self.ignore_list = set()
        self.list_performance = {}
        self.last_check_time = {}
        self.lead_history = {}  # Track lead counts over time
        self.lead_stagnant_time = 300  # 5 minutes in seconds
        self.queue_threshold = 5  # Minimum number of lists to keep in queue

    def replenish_queue(self, verify_performance_func) -> None:
        """Replenish the list queue if it's running low."""
        try:
            if len(self.list_ids) < self.queue_threshold:
                logger.info(f"List queue running low ({len(self.list_ids)} lists remaining)...")
                
                # Check failed lists that might be ready to try again
                recovered_lists = []
                for list_id in list(self.failed_list_ids):  # Create a copy to modify during iteration
                    if verify_performance_func(list_id):
                        recovered_lists.append(list_id)
                        self.failed_list_ids.remove(list_id)
                        logger.info(f"Recovered list {list_id} from failed lists - now performing well")
                
                # Add recovered lists to the queue
                if recovered_lists:
                    self.list_ids.extend(recovered_lists)
                    logger.info(f"Added {len(recovered_lists)} recovered lists to queue")
                
                logger.info(f"Queue status: {len(self.list_ids)} lists available")
                
        except Exception as e:
            logger.error(f"Error replenishing list queue: {e}")
            logger.error("Stack trace:", exc_info=True)

    def process_list_metrics(self, list_id: str, metrics: dict, 
                           low_conversion_lists: List[str], 
                           high_conversion_lists: List[str], 
                           low_contact_lists: List[str]):
        """Process metrics for a list and categorize it."""
        try:
            if list_id in self.ignore_list:
                return

            contacts = metrics.get('contact_count', 0)
            conversion = metrics.get('conversion_rate', 0)
            contact_rate = metrics.get('contact_rate', 0)
            is_active = metrics.get('is_active', False)
            has_leads = metrics.get('has_leads', False)
            lead_count = metrics.get('lead_count', 0)

            # Update performance tracking
            if list_id not in self.list_performance:
                self.list_performance[list_id] = []

            self.list_performance[list_id].append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "conversion_rate": conversion,
                "contact_count": contacts,
                "contact_rate": contact_rate,
                "is_active": is_active,
                "has_leads": has_leads,
                "lead_count": lead_count
            })

            # Apply thresholds
            if is_active:
                if contacts >= self.thresholds.contact_count:
                    if conversion < self.thresholds.conversion_rate_pct:
                        logger.info(f"Added {list_id} to low conversion lists (CR: {conversion:.2f}% < {self.thresholds.conversion_rate_pct:.2f}%, CC: {contacts} >= {self.thresholds.contact_count})")
                        low_conversion_lists.append(list_id)
                    if contacts >= self.thresholds.contact_rate_count:
                        if contact_rate < self.thresholds.contact_rate_pct:
                            logger.info(f"Added {list_id} to low contact rate lists (CTR: {contact_rate:.2f}% < {self.thresholds.contact_rate_pct:.2f}%, CC: {contacts} >= {self.thresholds.contact_rate_count})")
                            low_contact_lists.append(list_id)
            elif has_leads:  # Only process inactive lists that have leads
                if contacts >= self.thresholds.contact_count and conversion >= self.thresholds.conversion_rate_pct:
                    logger.info(f"Added {list_id} to high conversion lists (CR: {conversion:.2f}% >= {self.thresholds.conversion_rate_pct:.2f}%)")
                    high_conversion_lists.append(list_id)
                elif contacts < self.thresholds.contact_rate_count:
                    logger.info(f"Added {list_id} to low contact lists (CC: {contacts} < {self.thresholds.contact_rate_count})")
                    low_contact_lists.append(list_id)

        except Exception as e:
            logger.error(f"Error processing metrics for list {list_id}: {e}")
            logger.error("Stack trace:", exc_info=True)

    def process_list_changes(self, low_conv_lists: List[str], high_conv_lists: List[str], low_contact_lists: List[str], campaign_id: str):
        """Process necessary list changes based on performance data."""
        try:
            if not low_conv_lists:
                logger.info("No low-converting lists to change at this time")
                return

            logger.info("\n=== Processing List Changes ===")
            logger.info(f"Lists to replace: {low_conv_lists}")
            logger.info(f"Available high-converting lists: {high_conv_lists}")
            logger.info(f"Available low-contact lists: {low_contact_lists}")

            # Get current metrics to check active status
            current_metrics = self.portal_interface.get_campaign_metrics(campaign_id, self.metrics_history)
            
            # Filter out any high conversion lists that are currently active
            high_conv_lists = [
                list_id for list_id in high_conv_lists 
                if not (list_id in current_metrics and current_metrics[list_id].get('is_active', False))
            ]
            
            # Filter out any low contact lists that are currently active
            low_contact_lists = [
                list_id for list_id in low_contact_lists 
                if not (list_id in current_metrics and current_metrics[list_id].get('is_active', False))
            ]
            
            logger.info(f"Available inactive high-converting lists: {high_conv_lists}")
            logger.info(f"Available inactive low-contact lists: {low_contact_lists}")

            # Add failing lists to failed_list_ids
            self.failed_list_ids.update(low_conv_lists)
            
            # Process all low-converting lists
            for remove_list_id in low_conv_lists:
                new_list_id = self._get_replacement_list(high_conv_lists, low_contact_lists)
                
                if not new_list_id:
                    logger.info(f"No valid inactive replacement lists available for {remove_list_id}")
                    continue

                # Double check the new list is still inactive before making the change
                if new_list_id in current_metrics and current_metrics[new_list_id].get('is_active', False):
                    logger.info(f"Skipping replacement with {new_list_id} as it became active during processing")
                    continue

                # Attempt the list change
                if self.portal_interface.change_list(remove_list_id, new_list_id, campaign_id):
                    logger.info(f"Successfully swapped list {remove_list_id} with {new_list_id}")
                    
                    # Update active status in metrics history
                    if remove_list_id in self.metrics_history:
                        latest_metrics = self.metrics_history[remove_list_id].get('dashboard_metrics', [])
                        if latest_metrics:
                            latest_metrics[-1]['is_active'] = False
                            logger.info(f"Updated {remove_list_id} status to inactive in metrics history")
                    
                    if new_list_id in self.metrics_history:
                        latest_metrics = self.metrics_history[new_list_id].get('dashboard_metrics', [])
                        if latest_metrics:
                            latest_metrics[-1]['is_active'] = True
                            logger.info(f"Updated {new_list_id} status to active in metrics history")
                    
                    # Update tracking sets
                    self.used_list_ids.add(new_list_id)
                    self.used_list_ids.discard(remove_list_id)
                    self.failed_list_ids.discard(new_list_id)
                else:
                    self._handle_failed_change(new_list_id, high_conv_lists, low_contact_lists)

        except Exception as e:
            logger.error(f"Error processing list changes: {e}")
            logger.error("Stack trace:", exc_info=True)

    def _get_replacement_list(self, high_conv_lists: List[str], low_contact_lists: List[str]) -> Optional[str]:
        """Get a replacement list based on performance data."""
        try:
            # Get the appropriate campaign ID based on server type
            if self.server_config.server_type == ServerType.GMB:
                campaign_id = self.server_config.campaign_ids.get("fronter") or self.server_config.campaign_ids.get("main")
            else:  # OSD server
                campaign_id = self.server_config.campaign_ids["main"]
            
            # Get current metrics
            current_metrics = self.portal_interface.get_campaign_metrics(campaign_id)
            
            # Priority 1: High conversion lists
            for candidate in high_conv_lists:
                # Skip if list is active in current metrics
                if candidate in current_metrics and current_metrics[candidate].get('is_active', False):
                    logger.info(f"Skipping list {candidate} as it is currently active")
                    continue
                
                # Get list name from metrics if available
                list_name = current_metrics.get(candidate, {}).get('list_name', '')
                
                # Skip if list should be ignored
                if self._should_ignore_list(candidate, list_name):
                    logger.info(f"Skipping list {candidate} as it is in the ignore list or contains 'MLM'")
                    continue
                
                if (candidate not in self.list_manager.used_list_ids and 
                    self.portal_interface.verify_list_performance(candidate, campaign_id, self.metrics_history, self.thresholds)):
                    logger.info(f"Selected high-performing list {candidate} as replacement")
                    return candidate
            
            # Priority 2: Lists with low contact counts
            for candidate in low_contact_lists:
                # Skip if list is active in current metrics
                if candidate in current_metrics and current_metrics[candidate].get('is_active', False):
                    logger.info(f"Skipping list {candidate} as it is currently active")
                    continue
                
                # Get list name from metrics if available
                list_name = current_metrics.get(candidate, {}).get('list_name', '')
                
                # Skip if list should be ignored
                if self._should_ignore_list(candidate, list_name):
                    logger.info(f"Skipping list {candidate} as it is in the ignore list or contains 'MLM'")
                    continue
                
                if (candidate not in self.list_manager.used_list_ids and 
                    self.portal_interface.verify_list_performance(candidate, campaign_id, self.metrics_history, self.thresholds)):
                    logger.info(f"Selected low-contact list {candidate} as replacement")
                    return candidate
            
            # Priority 3: Lists from user-provided queue
            while self.list_manager.list_ids:
                candidate = self.list_manager.list_ids.pop(0)
                # Skip if list is active in current metrics
                if candidate in current_metrics and current_metrics[candidate].get('is_active', False):
                    logger.info(f"Skipping list {candidate} as it is currently active")
                    continue
                
                # Get list name from metrics if available
                list_name = current_metrics.get(candidate, {}).get('list_name', '')
                
                # Skip if list should be ignored
                if self._should_ignore_list(candidate, list_name):
                    logger.info(f"Skipping list {candidate} as it is in the ignore list or contains 'MLM'")
                    continue
                
                if (candidate not in self.list_manager.used_list_ids and 
                    self.portal_interface.verify_list_performance(candidate, campaign_id, self.metrics_history, self.thresholds)):
                    logger.info(f"Selected fresh list {candidate} from user-provided queue as replacement")
                    return candidate
            
            logger.info("No suitable inactive replacement lists found in any priority category")
            return None
            
        except Exception as e:
            logger.error(f"Error getting replacement list: {e}")
            logger.error("Stack trace:", exc_info=True)
            return None

    def _handle_failed_change(self, list_id: str, high_conv_lists: List[str], low_contact_lists: List[str]):
        """Handle a failed list change by returning the list to appropriate queue"""
        if list_id in self.list_manager.used_list_ids:
            high_conv_lists.insert(0, list_id)
        elif list_id in low_contact_lists:
            low_contact_lists.insert(0, list_id)
        else:
            self.list_manager.list_ids.insert(0, list_id)

class TeleseroBalancer:
    """Main class orchestrating the list balancing system"""
    def __init__(
        self,
        server_config: ServerConfig,
        portal_interface: WebPortalInterface,
        list_manager: ListManager
    ):
        """Initialize TeleseroBalancer"""
        self.server_config = server_config
        self.portal_interface = portal_interface
        self.list_manager = list_manager
        self.agent_verifier = list_manager.agent_verifier
        self.running = False
        self.last_check_time = {}
        self.thresholds = list_manager.thresholds
        self.ignore_list = load_ignore_list(server_config.server_id)
        self.metrics_history = {}  # Store historical metrics for all lists
        self.dialables_history = {}  # Track dialable counts over time
        self.dialables_stagnant_time = 180  # 3 minutes in seconds
        
        # Create base logs directory if it doesn't exist
        self.logs_dir = os.path.join(os.getcwd(), 'metrics_logs')
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
            logger.info(f"Created base metrics logs directory: {self.logs_dir}")
        
        logger.info(f"Starting balancer for server {server_config.server_id}")
        
        # Set default thresholds based on server type
        if server_config.server_type == ServerType.OSD:
            self.campaign_id = server_config.campaign_ids["main"]
        else:
            self.fronter_campaign = server_config.campaign_ids["fronter"]
            self.closer_campaign = server_config.campaign_ids["closer"]
            
    def _should_ignore_list(self, list_id: str, list_name: str) -> bool:
        """Check if a list should be ignored based on its ID or name"""
        # Check if list ID is in the ignore list
        if list_id in self.ignore_list or list_id in self.list_manager.ignore_list:
            return True
            
        # Check if list name contains "MLM" (case-insensitive)
        if list_name and "MLM" in list_name.upper():
            logger.info(f"Ignoring list {list_id} with name '{list_name}' because it contains 'MLM' (case-insensitive)")
            return True
            
        return False

    def _check_dialables_stagnation(self, list_id: str, current_dialables: int, current_time: float, source: str = 'strategy') -> bool:
        """Check if dialables count has been stagnant for the threshold period"""
        try:
            if list_id not in self.dialables_history:
                self.dialables_history[list_id] = []
            
            # Add current count with timestamp and source
            self.dialables_history[list_id].append({
                'count': current_dialables,
                'timestamp': current_time,
                'source': source
            })
            
            # Keep entries within an extended window for trend analysis
            extended_window = self.dialables_stagnant_time * 2  # Keep twice the window
            cutoff_time = current_time - extended_window
            self.dialables_history[list_id] = [
                entry for entry in self.dialables_history[list_id]
                if entry['timestamp'] >= cutoff_time
            ]
            
            # Get entries from the same source for consistent comparison
            source_entries = [
                entry for entry in self.dialables_history[list_id]
                if entry['source'] == source
            ]
            
            # Need at least 3 checks within the window to determine stagnation
            if len(source_entries) >= 3:
                # Sort entries by timestamp
                entries = sorted(source_entries, key=lambda x: x['timestamp'])
                
                # Get the time span of our checks
                time_span = entries[-1]['timestamp'] - entries[0]['timestamp']
                
                # Check if we have enough time coverage (at least 80% of stagnant_time)
                if time_span >= (self.dialables_stagnant_time * 0.8):
                    # Get counts and their timestamps for analysis
                    counts_with_time = [(e['count'], e['timestamp']) for e in entries]
                    
                    # Calculate time differences between consecutive readings
                    time_diffs = [t2 - t1 for (_, t1), (_, t2) in zip(counts_with_time[:-1], counts_with_time[1:])]
                    avg_time_diff = sum(time_diffs) / len(time_diffs) if time_diffs else 0
                    
                    # Get unique counts
                    unique_counts = set(c for c, _ in counts_with_time)
                    
                    # Check for stagnation
                    if len(unique_counts) == 1 and list(unique_counts)[0] > 0:
                        logger.info(f"List {list_id} dialables stagnant detection:")
                        logger.info(f"  Current count: {current_dialables}")
                        logger.info(f"  Stagnation duration: {time_span:.1f} seconds")
                        logger.info(f"  Average check interval: {avg_time_diff:.1f} seconds")
                        logger.info(f"  History: {', '.join([f'{c} @ ' + datetime.fromtimestamp(t).strftime('%H:%M:%S') for c, t in counts_with_time])}")
                        return True
                    
                    # Log changes and detect trends
                    if len(unique_counts) > 1:
                        # Calculate rate of change
                        first_count, first_time = counts_with_time[0]
                        last_count, last_time = counts_with_time[-1]
                        time_delta = last_time - first_time
                        count_delta = last_count - first_count
                        rate_of_change = count_delta / time_delta if time_delta > 0 else 0
                        
                        logger.info(f"List {list_id} dialables change detection:")
                        logger.info(f"  Current count: {current_dialables}")
                        logger.info(f"  Time span: {time_span:.1f} seconds")
                        logger.info(f"  Rate of change: {rate_of_change:.2f} per second")
                        logger.info(f"  History: {', '.join([f'{c} @ ' + datetime.fromtimestamp(t).strftime('%H:%M:%S') for c, t in counts_with_time])}")
            
            return False
                
        except Exception as e:
            logger.error(f"Error checking dialables stagnation for list {list_id}: {e}")
            logger.error("Stack trace:", exc_info=True)
            return False

    def _update_dialables_history(self, list_id: str, metrics: dict):
        """Update dialables history with new metrics"""
        try:
            current_time = time.time()
            
            # Initialize history if needed
            if list_id not in self.dialables_history:
                self.dialables_history[list_id] = []
            
            # Add new entry
            self.dialables_history[list_id].append({
                'count': metrics.get('dialables', 0),
                'timestamp': current_time,
                'source': 'dashboard',
                'is_active': metrics.get('is_active', False),
                'has_leads': metrics.get('has_leads', False)
            })
            
            # Clean up old entries
            cutoff_time = current_time - (self.dialables_stagnant_time * 2)  # Keep twice the window for analysis
            self.dialables_history[list_id] = [
                entry for entry in self.dialables_history[list_id]
                if entry['timestamp'] >= cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error updating dialables history for list {list_id}: {e}")
            logger.error("Stack trace:", exc_info=True)

    def _get_metrics_log_path(self) -> str:
        """Get the paths for today's metrics log files"""
        # Create server-specific directory if it doesn't exist
        server_dir = os.path.join(self.logs_dir, f"IB{self.server_config.server_id}")
        if not os.path.exists(server_dir):
            os.makedirs(server_dir)
            logger.info(f"Created server-specific log directory: {server_dir}")
        
        # Create date-specific directory
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_dir = os.path.join(server_dir, date_str)
        if not os.path.exists(date_dir):
            os.makedirs(date_dir)
            logger.info(f"Created date-specific log directory: {date_dir}")
        
        # Create single file per day for each metric type
        metrics_types = {
            'dashboard': f'dashboard_metrics_{date_str}.json',
            'strategy': f'strategy_metrics_{date_str}.json',
            'combined': f'combined_metrics_{date_str}.json'
        }
        
        log_files = {}
        for metric_type, filename in metrics_types.items():
            log_files[metric_type] = os.path.join(date_dir, filename)
        
        return log_files

    def _save_metrics_to_log(self, list_id: str, metrics: dict, source: str):
        """Save metrics to the daily log file"""
        try:
            log_files = self._get_metrics_log_path()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Format the metrics entry
            metrics_entry = {
                'timestamp': timestamp,
                'server_id': self.server_config.server_id,
                'server_type': self.server_config.server_type.value,
                'list_id': list_id,
                'source': source,
                **metrics
            }
            
            # Add campaign type for GMB servers
            if self.server_config.server_type == ServerType.GMB:
                metrics_entry['campaign_type'] = 'fronter' if metrics.get('is_active_fronter') else 'closer'
            
            # Save to appropriate log file based on source
            log_file = log_files.get(source, log_files['combined'])
            
            # Load existing entries if file exists
            existing_entries = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        existing_entries = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse existing log file {log_file}, starting new file")
                    existing_entries = []
            
            # Append new entry
            existing_entries.append(metrics_entry)
            
            # Write updated entries back to file
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(existing_entries, f, indent=2, default=str, sort_keys=True)
            
            # If we have combined metrics, save those too
            if list_id in self.metrics_history and self.metrics_history[list_id]['combined_metrics']:
                combined_log_file = log_files['combined']
                combined_metrics = self.metrics_history[list_id]['combined_metrics'][-1]  # Get latest combined metrics
                
                # Format the combined metrics entry
                combined_entry = {
                    'timestamp': timestamp,
                    'server_id': self.server_config.server_id,
                    'server_type': self.server_config.server_type.value,
                    'list_id': list_id,
                    'source': 'combined',
                    **combined_metrics
                }
                
                # Load existing combined entries
                existing_combined = []
                if os.path.exists(combined_log_file):
                    try:
                        with open(combined_log_file, 'r', encoding='utf-8') as f:
                            existing_combined = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse existing combined log file, starting new file")
                        existing_combined = []
                
                # Append new combined entry
                existing_combined.append(combined_entry)
                
                # Write updated combined entries back to file
                with open(combined_log_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_combined, f, indent=2, default=str, sort_keys=True)
            
            logger.debug(f"Saved metrics to {log_file}")
            
        except Exception as e:
            logger.error(f"Error saving metrics to log: {e}")
            logger.error("Stack trace:", exc_info=True)

    def _update_metrics_history(self, list_id: str, metrics: dict, source: str):
        """Update metrics history for a list, merging data from both sources"""
        try:
            current_time = time.time()
            
            if list_id not in self.metrics_history:
                self.metrics_history[list_id] = {
                    'strategy_metrics': [],
                    'dashboard_metrics': [],
                    'combined_metrics': [],  # Array for merged metrics
                    'first_seen': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'last_seen': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            
            # Update last seen timestamp
            self.metrics_history[list_id]['last_seen'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Handle dialables value before creating metrics entry
            if 'dialables' in metrics:
                # If dialables are marked as unavailable, try to get previous value
                if metrics.get('dialables_unavailable', False):
                    previous_metrics = None
                    if source == 'strategy' and self.metrics_history[list_id]['strategy_metrics']:
                        previous_metrics = self.metrics_history[list_id]['strategy_metrics'][-1]
                    elif source == 'dashboard' and self.metrics_history[list_id]['dashboard_metrics']:
                        previous_metrics = self.metrics_history[list_id]['dashboard_metrics'][-1]
                    
                    if previous_metrics and 'dialables' in previous_metrics:
                        logger.info(f"Dialables N/A for list {list_id}, using previous value: {previous_metrics['dialables']}")
                        metrics['dialables'] = previous_metrics['dialables']
                        metrics['has_leads'] = previous_metrics.get('has_leads', False)
                
                # If dialables is 0, verify if it's a real 0 or potential error
                elif metrics['dialables'] == 0 and metrics.get('is_active', False):
                    previous_metrics = None
                    if source == 'strategy' and self.metrics_history[list_id]['strategy_metrics']:
                        previous_metrics = self.metrics_history[list_id]['strategy_metrics'][-1]
                    elif source == 'dashboard' and self.metrics_history[list_id]['dashboard_metrics']:
                        previous_metrics = self.metrics_history[list_id]['dashboard_metrics'][-1]
                    
                    if previous_metrics and previous_metrics.get('dialables', 0) > 0:
                        # Only keep 0 if we've seen it multiple times
                        zero_count = sum(1 for m in self.metrics_history[list_id][f'{source}_metrics'][-3:]
                                       if m.get('dialables', 1) == 0)
                        if zero_count < 2:  # If we haven't seen 0 multiple times
                            logger.info(f"Suspicious 0 dialables for active list {list_id}, using previous value: {previous_metrics['dialables']}")
                            metrics['dialables'] = previous_metrics['dialables']
                            metrics['has_leads'] = previous_metrics.get('has_leads', True)
            
            # Add new metrics with timestamp
            metrics_entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'source': source,
                **metrics
            }
            
            # Check for stagnant dialables if we have the count
            if 'dialables' in metrics_entry and not metrics.get('dialables_unavailable', False):
                is_stagnant = self._check_dialables_stagnation(
                    list_id, 
                    metrics_entry['dialables'], 
                    current_time,
                    source
                )
                metrics_entry['dialables_stagnant'] = is_stagnant
                
                # If stagnant, update the metrics to reflect this
                if is_stagnant:
                    metrics_entry['has_leads'] = False
                    metrics_entry['lead_count'] = 0
                    logger.info(f"List {list_id} marked as empty due to stagnant dialables")
            
            # Store metrics based on source - keep all entries for the day
            if source == 'strategy':
                self.metrics_history[list_id]['strategy_metrics'].append(metrics_entry)
            else:  # dashboard
                self.metrics_history[list_id]['dashboard_metrics'].append(metrics_entry)
            
            # Merge metrics from both sources
            latest_strategy = None
            latest_dashboard = None
            
            # Get latest strategy metrics
            if self.metrics_history[list_id]['strategy_metrics']:
                latest_strategy = self.metrics_history[list_id]['strategy_metrics'][-1]
            
            # Get latest dashboard metrics
            if self.metrics_history[list_id]['dashboard_metrics']:
                latest_dashboard = self.metrics_history[list_id]['dashboard_metrics'][-1]
            
            # Create merged metrics if we have both sources
            if latest_strategy and latest_dashboard:
                # Start with dashboard metrics as base
                merged_metrics = latest_dashboard.copy()
                
                # Add/update with strategy metrics, preserving good dialables data
                strategy_fields = {
                    'percent_blend': 'percent_blend',
                    'resets': 'resets',
                    'last_reset': 'last_reset',
                    'reset_today': 'reset_today',
                    'list_name': 'list_name',
                    'priority': 'priority',
                    'mix_name': 'mix_name',
                    'mix_method': 'mix_method'
                }
                
                # Special handling for dialables
                if 'dialables' in latest_strategy and not latest_strategy.get('dialables_unavailable', False):
                    if ('dialables' not in merged_metrics or 
                        merged_metrics.get('dialables_unavailable', False) or 
                        (merged_metrics['dialables'] == 0 and latest_strategy['dialables'] > 0)):
                        merged_metrics['dialables'] = latest_strategy['dialables']
                        merged_metrics['has_leads'] = latest_strategy.get('has_leads', True)
                
                for strat_key, merged_key in strategy_fields.items():
                    if strat_key in latest_strategy:
                        merged_metrics[merged_key] = latest_strategy[strat_key]
                
                # Add timestamp of merge
                merged_metrics['merge_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                merged_metrics['dashboard_timestamp'] = latest_dashboard['timestamp']
                merged_metrics['strategy_timestamp'] = latest_strategy['timestamp']
                
                # Store merged metrics - keep all entries for the day
                self.metrics_history[list_id]['combined_metrics'].append(merged_metrics)
                
                # Log merged metrics summary
                logger.debug(f"Merged metrics for list {list_id}:")
                logger.debug(f"  Active: {merged_metrics.get('is_active', False)}")
                logger.debug(f"  Has Leads: {merged_metrics.get('has_leads', False)}")
                logger.debug(f"  Lead Count: {merged_metrics.get('lead_count', 0)}")
                logger.debug(f"  Dialables: {merged_metrics.get('dialables', 0)}")
                logger.debug(f"  Contact Rate: {merged_metrics.get('contact_rate', 0):.2f}%")
                logger.debug(f"  Conversion Rate: {merged_metrics.get('conversion_rate', 0):.2f}%")
                if 'percent_blend' in merged_metrics:
                    logger.debug(f"  Blend Percentage: {merged_metrics['percent_blend']:.1f}%")
                if 'priority' in merged_metrics:
                    logger.debug(f"  Priority: {merged_metrics['priority']}")
            
            # Save to daily log file
            self._save_metrics_to_log(list_id, metrics_entry, source)
            
        except Exception as e:
            logger.error(f"Error updating metrics history for list {list_id}: {e}")
            logger.error("Stack trace:", exc_info=True)

    def start(self):
        """Start the balancing process"""
        try:
            logger.info(f"Starting balancer for server {self.server_config.server_id}")
            self.portal_interface.login(self.server_config.username, self.server_config.password)
            self.running = True
            
            while self.running:
                try:
                    self._process_campaigns()
                    # Use 60-second check interval
                    time.sleep(60)
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(60)  # Keep consistent 60-second retry on error
        except Exception as e:
            logger.error(f"Fatal error in balancer: {e}")
            self.stop()
            raise

    def stop(self):
        """Stop the balancing process"""
        logger.info("Stopping balancer")
        self.running = False

    def _process_campaigns(self):
        """Process all campaigns for the server"""
        is_osd = self.server_config.server_type == ServerType.OSD
        
        if is_osd:
            self._process_osd_campaign()
        else:
            self._process_gmb_campaigns()
        
        # Replenish queue if needed
        self.list_manager.replenish_queue(self.portal_interface.verify_list_performance)

    def _process_osd_campaign(self):
        """Process OSD campaign metrics and make necessary changes."""
        try:
            campaign_id = self.server_config.campaign_ids["main"]
            logger.info(f"Processing OSD campaign {campaign_id}")
            
            current_time = time.time()
            active_strategy_lists = set()  # Track lists active in dialing strategy
            
            # Check if we should get dialing strategy metrics
            should_check_strategy = (
                'last_strategy_check' not in self.__dict__ or 
                current_time - self.last_strategy_check >= 300  # 5 minutes
            )
            
            # Always get dialing strategy metrics if it's the first check or if enough time has passed
            if should_check_strategy:
                logger.info("Getting dialing strategy metrics...")
                strategy_metrics = self.portal_interface.get_dialing_strategy_metrics(campaign_id)
                if strategy_metrics:
                    logger.info("Successfully retrieved dialing strategy metrics")
                    self.last_strategy_check = current_time
                    
                    # Log current list statuses and update history
                    logger.info("\n=== Current List Status ===")
                    for list_id, data in strategy_metrics.items():
                        # Add to active strategy lists set
                        active_strategy_lists.add(list_id)
                        
                        # Check for dialables stagnation if list is active
                        dialables = data.get('dialables', 0)
                        data['has_leads'] = dialables > 0  # Derive has_leads from dialables
                        
                        if data.get('is_active', False):
                            if self._check_dialables_stagnation(list_id, dialables, current_time):
                                data['has_leads'] = False
                                data['lead_count'] = 0
                                logger.info(f"List {list_id} marked as empty due to stagnant dialables")
                        
                        # Update metrics history
                        data['is_active'] = True  # Mark as active since it's in dialing strategy
                        self._update_metrics_history(list_id, data, 'strategy')
                        
                        logger.info(f"\nList {list_id} ({data['list_name']}):")
                        logger.info(f"  Blend: {data['percent_blend']:.1f}%")
                        logger.info(f"  Dialables: {dialables}")
                        logger.info(f"  Resets: {data['resets']}")
                        logger.info(f"  Last Reset: {data['last_reset']}")
                        logger.info(f"  Reset Today: {'Yes' if data['reset_today'] else 'No'}")
                        if not data['has_leads']:
                            logger.info(f"  Status: LEADS EMPTY (Stagnant Dialables)")
                    
                    # Return to dashboard after checking dialing strategy
                    logger.info("Returning to dashboard...")
                    self.portal_interface.driver.get(self.portal_interface.url)
                    time.sleep(5)  # Wait for dashboard to load
            
            # Verify agents are present
            if not self.agent_verifier.verify_agents(self.portal_interface.driver, campaign_id, "ANY"):
                logger.info("No valid ANY agents present.")
                logger.info("Waiting 60 seconds before checking agents again...")
                time.sleep(60)
                return
            
            # Select campaign and get metrics
            if not self.portal_interface.select_campaign(campaign_id):
                logger.error("Failed to select campaign")
                return
                
            # Get metrics for all lists in one pass
            metrics = self.portal_interface.get_campaign_metrics(campaign_id)
            if not metrics:
                logger.error("Failed to get campaign metrics")
                return
            
            # Update metrics history with dashboard metrics
            for list_id, list_metrics in metrics.items():
                # If list is in dialing strategy, mark it as active
                if list_id in active_strategy_lists:
                    list_metrics['is_active'] = True
                self._update_metrics_history(list_id, list_metrics, 'dashboard')
            
            # Merge strategy metrics into main metrics if we have them
            if should_check_strategy and strategy_metrics:
                for list_id, strat_data in strategy_metrics.items():
                    if list_id in metrics:
                        metrics[list_id].update({
                            'percent_blend': strat_data['percent_blend'],
                            'dialables': strat_data['dialables'],
                            'resets': strat_data['resets'],
                            'last_reset': strat_data['last_reset'],
                            'reset_today': strat_data['reset_today'],
                            'list_name': strat_data['list_name'],
                            'priority': strat_data['priority'],
                            'is_active': True  # Always mark as active if in dialing strategy
                        })
                    else:
                        # If list is in strategy but not in dashboard metrics, add it
                        metrics[list_id] = {
                            'contact_count': 0,
                            'contact_rate': 0.0,
                            'conversion_rate': 0.0,
                            'is_active': True,  # Mark as active since it's in dialing strategy
                            'has_leads': strat_data['dialables'] > 0,
                            'lead_count': strat_data['dialables'],
                            'sales_count': 0,
                            'percent_blend': strat_data['percent_blend'],
                            'dialables': strat_data['dialables'],
                            'resets': strat_data['resets'],
                            'last_reset': strat_data['last_reset'],
                            'reset_today': strat_data['reset_today'],
                            'list_name': strat_data['list_name'],
                            'priority': strat_data['priority']
                        }
            
            # Initialize lists for tracking changes
            low_conversion_lists = []
            high_conversion_lists = []
            low_contact_lists = []
            active_lists = []
            inactive_lists = []
            
            # First pass: Process and categorize all lists
            logger.info("\n=== Processing Dashboard Metrics ===")
            for list_id, list_metrics in metrics.items():
                # Skip ignored lists
                if self._should_ignore_list(list_id, list_metrics.get('list_name', '')):
                    logger.info(f"Skipping ignored list {list_id}")
                    continue
                
                # Extract all metrics
                contacts = list_metrics.get('contact_count', 0)
                conversion = list_metrics.get('conversion_rate', 0.0)
                contact_rate = list_metrics.get('contact_rate', 0.0)
                is_active = list_metrics.get('is_active', False)
                has_leads = list_metrics.get('has_leads', False)
                lead_count = list_metrics.get('lead_count', 0)
                dialables = list_metrics.get('dialables', 0)  # Get dialables from merged metrics

                # Log metrics for all lists
                logger.info(f"\nList {list_id}:")
                logger.info(f"  Status: {'Active' if is_active else 'Inactive'}")
                logger.info(f"  Has Leads: {has_leads}")
                logger.info(f"  Lead Count: {lead_count}")
                if is_active:
                    logger.info(f"  Dialables: {dialables}")
                logger.info(f"  Contacts: {contacts}")
                logger.info(f"  Contact Rate: {contact_rate:.2f}%")
                logger.info(f"  Conversion Rate: {conversion:.2f}%")
                logger.info(f"  Total Appointments: {list_metrics['sales_count']}")
                
                # Check for stagnant dialables if active
                if is_active and dialables is not None:
                    # Skip stagnation check if dialables were unavailable
                    if list_metrics.get('dialables_unavailable', False):
                        logger.info(f"  Status: DIALABLES UNAVAILABLE (Using previous: {dialables})")
                    elif self._check_dialables_stagnation(list_id, dialables, current_time):
                        # Check if list was already reset today
                        if list_metrics.get('reset_today', False):
                            logger.info(f"  Status: LIST INELIGIBLE (Already Reset Today, Last Reset: {list_metrics.get('last_reset', 'Unknown')})")
                            has_leads = False
                            lead_count = 0
                            list_metrics['has_leads'] = False
                            list_metrics['lead_count'] = 0
                        # If not reset today, check conversion rate
                        else:
                            if conversion >= self.thresholds.conversion_rate:
                                logger.info(f"  Status: HIGH CONVERSION - NEEDS RESET (CR: {conversion:.2f}% >= {self.thresholds.conversion_rate:.2f}%, Last Reset: {list_metrics.get('last_reset', 'Unknown')})")
                                list_metrics['needs_reset'] = True
                                continue  # Skip further processing to prevent replacement
                            # If conversion is poor, mark as empty
                            else:
                                logger.info(f"  Status: LEADS EMPTY (Stagnant Dialables)")
                                has_leads = False
                                lead_count = 0
                                list_metrics['has_leads'] = False
                                list_metrics['lead_count'] = 0
                
                # Categorize lists based on status and metrics
                if is_active:
                    active_lists.append(list_id)
                    # Only check performance if list has leads and doesn't need reset
                    if has_leads and not list_metrics.get('needs_reset', False):
                        # Always check conversion rate first, regardless of contact count
                        if conversion >= self.thresholds.conversion_rate:
                            logger.info(f"  List has good conversion rate ({conversion:.2f}% >= {self.thresholds.conversion_rate:.2f}%) - keeping list")
                            continue
                        
                        # If conversion is poor and we have enough contacts to be sure, mark for replacement
                        if contacts >= self.thresholds.contact_count and conversion < self.thresholds.conversion_rate:
                            logger.info(f"  Action: Added to low conversion lists (CR: {conversion:.2f}% < {self.thresholds.conversion_rate:.2f}%, CC: {contacts} >= {self.thresholds.contact_count})")
                            low_conversion_lists.append(list_id)
                        # If we have enough contacts to evaluate contact rate but not conversion
                        elif contacts >= self.thresholds.contact_rate_count:
                            # If contact rate is good, keep trying for conversion
                            if contact_rate >= self.thresholds.contact_rate_pct:
                                logger.info(f"  Status: Good contact rate ({contact_rate:.2f}% >= {self.thresholds.contact_rate_pct:.2f}%), needs more contacts for conversion evaluation")
                                continue
                            else:
                                logger.info(f"  Action: Added to low contact lists (CTR: {contact_rate:.2f}% < {self.thresholds.contact_rate_pct:.2f}%)")
                                low_contact_lists.append(list_id)
                    elif not has_leads and not list_metrics.get('needs_reset', False):  # Only add to low conversion if not marked for reset
                        logger.info(f"  Action: Added to low conversion lists (No Leads)")
                        low_conversion_lists.append(list_id)
                else:
                    inactive_lists.append(list_id)
                    # Always check conversion rate first for inactive lists too
                    if has_leads:
                        if conversion >= self.thresholds.conversion_rate:
                            logger.info(f"  Action: Added to high conversion lists (CR: {conversion:.2f}% >= {self.thresholds.conversion_rate:.2f}%)")
                            high_conversion_lists.append(list_id)
                        # Then check if list has enough contacts to evaluate contact rate
                        elif contacts >= self.thresholds.contact_rate_count:
                            # If contact rate is good, add to high conv lists to try again
                            if contact_rate >= self.thresholds.contact_rate_pct:
                                logger.info(f"  Action: Added to high conversion lists (Good Contact Rate: {contact_rate:.2f}% >= {self.thresholds.contact_rate_pct:.2f}%, needs more contacts for conversion evaluation)")
                                high_conversion_lists.append(list_id)
                            else:
                                logger.info(f"  Action: Added to low contact lists (Poor Contact Rate: {contact_rate:.2f}% < {self.thresholds.contact_rate_pct:.2f}%)")
                                low_contact_lists.append(list_id)
                        else:
                            logger.info(f"  Action: Added to low contact lists (CC: {contacts} < {self.thresholds.contact_rate_count})")
                            low_contact_lists.append(list_id)
            
            # Summary of current state
            logger.info("\n=== Campaign Status Summary ===")
            logger.info(f"Active Lists: {len(active_lists)}")
            logger.info(f"Inactive Lists: {len(inactive_lists)}")
            logger.info(f"Low Conversion Lists: {len(low_conversion_lists)}")
            logger.info(f"High Conversion Lists: {len(high_conversion_lists)}")
            logger.info(f"Low Contact Lists: {len(low_contact_lists)}")
            
            # Process necessary list changes immediately if needed
            lists_to_change = low_conversion_lists + low_contact_lists
            if lists_to_change:
                logger.info("\n=== Processing List Changes ===")
                logger.info(f"Lists to replace: {lists_to_change}")
                logger.info(f"Available high-converting lists: {high_conversion_lists}")
                logger.info(f"Available low-contact lists: {low_contact_lists}")
                
                for remove_list_id in lists_to_change:
                    try:
                        new_list_id = self._get_replacement_list(high_conversion_lists, low_contact_lists)
                        if not new_list_id:
                            logger.info(f"No valid replacement lists available for {remove_list_id}, continuing to next list...")
                            continue

                        if self.portal_interface.change_list(remove_list_id, new_list_id, campaign_id):
                            logger.info(f"Successfully replaced list {remove_list_id} with {new_list_id}")
                            self.list_manager.used_list_ids.add(new_list_id)
                            self.list_manager.used_list_ids.discard(remove_list_id)
                        else:
                            logger.error(f"Failed to replace list {remove_list_id} with {new_list_id}, continuing to next list...")
                            self._handle_failed_change(new_list_id, high_conversion_lists, low_contact_lists)
                    except Exception as e:
                        logger.error(f"Error processing list change for {remove_list_id}: {e}")
                        logger.error("Stack trace:", exc_info=True)
                        logger.info("Continuing to next list...")
                        continue
            else:
                logger.info("\nNo list changes needed at this time")
        
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.error("Stack trace:", exc_info=True)

    def _process_gmb_campaigns(self):
        """Process GMB server campaigns"""
        try:
            # Get campaign IDs
            fronter_campaign = self.server_config.campaign_ids["fronter"]
            closer_campaign = self.server_config.campaign_ids["closer"]
            
            # Track metrics collection success
            metrics_collected = {
                'fronter': False,
                'closer': False
            }
            
            max_retries = 3
            retry_delay = 10  # seconds
            
            # Collect Fronter Metrics
            fronter_metrics = None
            for attempt in range(max_retries):
                try:
                    # Navigate to monitoring page if needed
                    if not self.portal_interface.driver.current_url.endswith("/monitoring/"):
                        self.portal_interface.driver.get(self.portal_interface.url)
                        time.sleep(5)
                    
                    # Switch to Fronter campaign
                    if not self.portal_interface.select_campaign(fronter_campaign):
                        logger.error(f"Failed to select Fronter campaign {fronter_campaign} (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    
                    time.sleep(5)  # Wait for campaign switch
                    
                    # Verify Fronter agents
                    if not self.list_manager.agent_verifier.verify_agents(
                        self.portal_interface.driver, fronter_campaign, "FRONTERS"
                    ):
                        logger.info("No valid Fronter agents present. Waiting...")
                        time.sleep(30)
                        return
                    
                    # Get Fronter metrics
                    fronter_metrics = self.portal_interface.get_campaign_metrics(fronter_campaign)
                    if fronter_metrics:
                        metrics_collected['fronter'] = True
                        break
                    
                    logger.error(f"Failed to get Fronter metrics (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    
                except Exception as e:
                    logger.error(f"Error collecting Fronter metrics (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
            
            if not metrics_collected['fronter']:
                logger.error("Failed to collect Fronter metrics after all retries")
                return
            
            # Collect Closer Metrics
            closer_metrics = None
            for attempt in range(max_retries):
                try:
                    # Switch to Closer campaign
                    if not self.portal_interface.select_campaign(closer_campaign):
                        logger.error(f"Failed to select Closer campaign {closer_campaign} (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    
                    time.sleep(5)  # Wait for campaign switch
                    
                    # Verify Closer agents
                    if not self.list_manager.agent_verifier.verify_agents(
                        self.portal_interface.driver, closer_campaign, "CLOSERS"
                    ):
                        logger.info("No valid Closer agents present. Waiting...")
                        time.sleep(30)
                        return
                    
                    # Get Closer metrics
                    closer_metrics = self.portal_interface.get_campaign_metrics(closer_campaign)
                    if closer_metrics:
                        metrics_collected['closer'] = True
                        break
                    
                    logger.error(f"Failed to get Closer metrics (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    
                except Exception as e:
                    logger.error(f"Error collecting Closer metrics (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
            
            if not metrics_collected['closer']:
                logger.error("Failed to collect Closer metrics after all retries")
                return
            
            # Lists that need attention
            low_conv_lists = []
            high_conv_lists = []
            low_contact_lists = []
            
            # Track lists present in each campaign
            fronter_list_ids = set(fronter_metrics.keys())
            closer_list_ids = set(closer_metrics.keys())
            all_list_ids = fronter_list_ids.union(closer_list_ids)
            
            # Log campaign list discrepancies
            lists_only_in_fronter = fronter_list_ids - closer_list_ids
            lists_only_in_closer = closer_list_ids - fronter_list_ids
            if lists_only_in_fronter:
                logger.warning(f"Lists only in Fronter campaign: {lists_only_in_fronter}")
            if lists_only_in_closer:
                logger.warning(f"Lists only in Closer campaign: {lists_only_in_closer}")
            
            # Process metrics for each list
            logger.info("\n=== Processing GMB Campaign Metrics ===")
            for list_id in all_list_ids:
                # Get list name from either fronter or closer metrics
                list_name = ''
                if list_id in fronter_metrics:
                    list_name = fronter_metrics[list_id].get('list_name', '')
                elif list_id in closer_metrics:
                    list_name = closer_metrics[list_id].get('list_name', '')
                
                # Skip ignored lists
                if self._should_ignore_list(list_id, list_name):
                    logger.info(f"Skipping ignored list {list_id}")
                    continue
                
                # Get metrics from both campaigns
                fronter_stats = fronter_metrics.get(list_id, {
                    'contact_count': 0,
                    'contact_rate': 0.0,
                    'is_active': False,
                    'has_leads': False,
                    'lead_count': 0
                })
                
                closer_stats = closer_metrics.get(list_id, {
                    'contact_count': 0,  # This represents transfers
                    'is_active': False,
                    'has_leads': False
                })
                
                # Calculate metrics
                fronter_contacts = fronter_stats.get('contact_count', 0)
                closer_contacts = closer_stats.get('contact_count', 0)  # These are transfers
                fronter_contact_rate = fronter_stats.get('contact_rate', 0.0)  # Get contact rate from fronter only
                
                # Calculate transfer rate (conversion) only if we have fronter contacts
                transfer_rate = (closer_contacts / fronter_contacts * 100) if fronter_contacts > 0 else 0.0
                
                # Determine active status across both campaigns first
                is_active_fronter = fronter_stats.get('is_active', False)
                is_active_closer = closer_stats.get('is_active', False)
                is_active = is_active_fronter or is_active_closer  # List is considered active if it's active in either campaign
                
                # Get dialables and lead counts for stagnation tracking
                current_time = time.time()
                
                # For inactive lists, try to get last known dialables from history
                if not is_active_fronter and list_id in self.metrics_history:
                    # Look for most recent active metrics
                    active_metrics = [m for m in reversed(self.metrics_history[list_id].get('dashboard_metrics', []))
                                    if m.get('is_active_fronter', False)]
                    if active_metrics:
                        # Use the last known dialables from when list was active
                        fronter_dialables = active_metrics[0].get('dialables', 0)
                        fronter_leads = active_metrics[0].get('lead_count', 0)
                        logger.info(f"  Using last known dialables ({fronter_dialables}) from when list was active")
                    else:
                        fronter_dialables = fronter_stats.get('dialables', 0)
                        fronter_leads = fronter_stats.get('lead_count', 0)
                else:
                    fronter_dialables = fronter_stats.get('dialables', 0)
                    fronter_leads = fronter_stats.get('lead_count', 0)
                
                # Check for stagnant dialables in active lists
                is_stagnant = False
                if is_active_fronter and fronter_dialables is not None:
                    # Skip stagnation check if dialables were unavailable
                    if fronter_stats.get('dialables_unavailable', False):
                        logger.info(f"  Status: DIALABLES UNAVAILABLE (Using previous: {fronter_dialables})")
                    elif self._check_dialables_stagnation(list_id, fronter_dialables, current_time, 'dashboard'):
                        # Check if list was already reset today
                        if fronter_stats.get('reset_today', False):
                            logger.info(f"  Status: LIST INELIGIBLE (Already Reset Today, Last Reset: {fronter_stats.get('last_reset', 'Unknown')})")
                            fronter_stats['has_leads'] = False
                            fronter_stats['lead_count'] = 0
                            is_stagnant = True
                        # If not reset today, check transfer rate
                        else:
                            if transfer_rate >= self.thresholds.conversion_rate:
                                logger.info(f"  Status: HIGH CONVERSION - NEEDS RESET (TR: {transfer_rate:.2f}% >= {self.thresholds.conversion_rate:.2f}%, Last Reset: {fronter_stats.get('last_reset', 'Unknown')})")
                                fronter_stats['needs_reset'] = True
                            else:
                                logger.info(f"  Status: LEADS EMPTY (Stagnant Dialables)")
                                fronter_stats['has_leads'] = False
                                fronter_stats['lead_count'] = 0
                                is_stagnant = True
                
                # Update has_leads status based on stagnation check
                has_leads = fronter_stats.get('has_leads', False) and not is_stagnant
                
                # Log detailed metrics
                logger.info(f"\nList {list_id}:")
                logger.info(f"  Present in Fronter: {list_id in fronter_metrics}")
                logger.info(f"  Present in Closer: {list_id in closer_metrics}")
                logger.info(f"  Active in Fronter: {is_active_fronter}")
                logger.info(f"  Active in Closer: {is_active_closer}")
                logger.info(f"  Overall Active Status: {is_active}")
                logger.info(f"  Fronter Contacts: {fronter_contacts}")
                logger.info(f"  Closer Transfers: {closer_contacts}")
                logger.info(f"  Transfer Rate: {transfer_rate:.2f}%")
                logger.info(f"  Fronter Contact Rate: {fronter_contact_rate:.2f}%")
                
                # Track historical metrics
                combined_metrics = {
                    'contact_count': fronter_contacts,
                    'contact_rate': fronter_contact_rate,  # Use fronter contact rate only
                    'conversion_rate': transfer_rate,  # Use transfer rate as conversion
                    'is_active': is_active,  # Use combined active status
                    'is_active_fronter': is_active_fronter,  # Track individual campaign status
                    'is_active_closer': is_active_closer,  # Track individual campaign status
                    'has_leads': has_leads,
                    'lead_count': fronter_stats.get('lead_count', 0),
                    'transfers': closer_contacts,  # Track transfers separately
                    'in_fronter': list_id in fronter_metrics,
                    'in_closer': list_id in closer_metrics,
                    'timestamp': time.time()
                }
                
                # Update metrics history
                self._update_metrics_history(list_id, combined_metrics, 'dashboard')
                
                # Process metrics for list categorization
                if is_active:  # Use combined active status for categorization
                    # Check if list has enough contacts for evaluation
                    if fronter_contacts >= self.thresholds.contact_count:
                        # Check transfer rate against conversion threshold
                        if transfer_rate < self.thresholds.conversion_rate:
                            logger.info(f"  Action: Added to low conversion lists (Transfer Rate: {transfer_rate:.2f}% < {self.thresholds.conversion_rate:.2f}%)")
                            low_conv_lists.append(list_id)
                        else:
                            logger.info(f"  Status: Good performance (Transfer Rate: {transfer_rate:.2f}% >= {self.thresholds.conversion_rate:.2f}%)")
                    # If we have enough fronter contacts for contact rate evaluation but not conversion
                    elif fronter_contacts >= self.thresholds.contact_rate_count:
                        # If fronter contact rate is good, keep trying for conversion
                        fronter_contact_rate = fronter_stats.get('contact_rate', 0.0)
                        if fronter_contact_rate >= self.thresholds.contact_rate_pct:
                            logger.info(f"  Status: Good fronter contact rate ({fronter_contact_rate:.2f}% >= {self.thresholds.contact_rate_pct:.2f}%), continuing to test for conversion")
                            continue  # Keep running the list
                        else:
                            logger.info(f"  Action: Added to low contact lists (Fronter Contact Rate: {fronter_contact_rate:.2f}% < {self.thresholds.contact_rate_pct:.2f}%)")
                            low_contact_lists.append(list_id)
                    # If not enough fronter contacts for either evaluation
                    else:
                        logger.info(f"  Status: Not enough fronter contacts for evaluation yet (Contacts: {fronter_contacts} < {self.thresholds.contact_rate_count})")
                        continue  # Keep running the list
                else:  # Inactive in both campaigns
                    if fronter_contacts > 0:  # Only evaluate lists with some fronter contact history
                        # First check if list has good transfer rate
                        if transfer_rate >= self.thresholds.conversion_rate:
                            logger.info(f"  Action: Added to high conversion lists (Transfer Rate: {transfer_rate:.2f}% >= {self.thresholds.conversion_rate:.2f}%)")
                            high_conv_lists.append(list_id)
                        # If past fronter contact threshold, only consider fronter contact rate if good
                        elif fronter_contacts >= self.thresholds.contact_rate_count:
                            # Check if we have enough fronter contacts to evaluate conversion
                            if fronter_contacts >= self.thresholds.contact_count:
                                # If conversion rate is poor, don't reactivate
                                if transfer_rate < self.thresholds.conversion_rate:
                                    logger.info(f"  Status: Poor transfer rate ({transfer_rate:.2f}% < {self.thresholds.conversion_rate:.2f}%) with sufficient fronter contacts ({fronter_contacts} >= {self.thresholds.contact_count})")
                                    continue
                            # If not enough contacts for conversion but good fronter contact rate, add to high conv to test
                            fronter_contact_rate = fronter_stats.get('contact_rate', 0.0)
                            if fronter_contact_rate >= self.thresholds.contact_rate_pct:
                                logger.info(f"  Action: Added to high conversion lists (Good Fronter Contact Rate: {fronter_contact_rate:.2f}% >= {self.thresholds.contact_rate_pct:.2f}%), worth testing for conversion")
                                high_conv_lists.append(list_id)
                            else:
                                logger.info(f"  Status: Poor fronter contact rate ({fronter_contact_rate:.2f}% < {self.thresholds.contact_rate_pct:.2f}%), not worth retesting")
                        # If not enough fronter contacts yet, add to low contact lists
                        else:
                            logger.info(f"  Action: Added to low contact lists (Fronter Contacts: {fronter_contacts} < {self.thresholds.contact_rate_count})")
                            low_contact_lists.append(list_id)
            
            # Summary of current state
            logger.info("\n=== Campaign Status Summary ===")
            logger.info(f"Total Lists: {len(all_list_ids)}")
            logger.info(f"Lists in Fronter: {len(fronter_list_ids)}")
            logger.info(f"Lists in Closer: {len(closer_list_ids)}")
            logger.info(f"Lists to Replace: {len(low_conv_lists)}")
            logger.info(f"High Conversion Lists Available: {len(high_conv_lists)}")
            logger.info(f"Low Contact Lists Available: {len(low_contact_lists)}")
            
            # Process necessary list changes
            if low_conv_lists:
                logger.info("\n=== Processing List Changes ===")
                logger.info(f"Lists to replace: {low_conv_lists}")
                logger.info(f"Available high-converting lists: {high_conv_lists}")
                logger.info(f"Available low-contact lists: {low_contact_lists}")
                
                for remove_list_id in low_conv_lists:
                    new_list_id = self._get_replacement_list(high_conv_lists, low_contact_lists)
                    if new_list_id:
                        if self.portal_interface.change_list(remove_list_id, new_list_id, fronter_campaign):
                            logger.info(f"Successfully replaced list {remove_list_id} with {new_list_id}")
                            self.list_manager.used_list_ids.add(new_list_id)
                            self.list_manager.used_list_ids.discard(remove_list_id)
                        else:
                            logger.error(f"Failed to replace list {remove_list_id} with {new_list_id}")
                            self._handle_failed_change(new_list_id, high_conv_lists, low_contact_lists)
            else:
                logger.info("\nNo list changes needed at this time")
            
        except Exception as e:
            logger.error(f"Error processing GMB campaigns: {e}")
            logger.error("Stack trace:", exc_info=True)

    def _get_replacement_list(self, high_conv_lists: List[str], low_contact_lists: List[str]) -> Optional[str]:
        """Get a replacement list based on performance data."""
        try:
            # Get the appropriate campaign ID based on server type
            if self.server_config.server_type == ServerType.GMB:
                campaign_id = self.server_config.campaign_ids.get("fronter") or self.server_config.campaign_ids.get("main")
            else:  # OSD server
                campaign_id = self.server_config.campaign_ids["main"]
            
            # Get current metrics
            current_metrics = self.portal_interface.get_campaign_metrics(campaign_id)
            
            # Priority 1: High conversion lists
            for candidate in high_conv_lists:
                # Skip if list is active in current metrics
                if candidate in current_metrics and current_metrics[candidate].get('is_active', False):
                    logger.info(f"Skipping list {candidate} as it is currently active")
                    continue
                
                # Get list name from metrics if available
                list_name = current_metrics.get(candidate, {}).get('list_name', '')
                
                # Skip if list should be ignored
                if self._should_ignore_list(candidate, list_name):
                    logger.info(f"Skipping list {candidate} as it is in the ignore list or contains 'MLM'")
                    continue
                
                if (candidate not in self.list_manager.used_list_ids and 
                    self.portal_interface.verify_list_performance(candidate, campaign_id, self.metrics_history, self.thresholds)):
                    logger.info(f"Selected high-performing list {candidate} as replacement")
                    return candidate
            
            # Priority 2: Lists with low contact counts
            for candidate in low_contact_lists:
                # Skip if list is active in current metrics
                if candidate in current_metrics and current_metrics[candidate].get('is_active', False):
                    logger.info(f"Skipping list {candidate} as it is currently active")
                    continue
                
                # Get list name from metrics if available
                list_name = current_metrics.get(candidate, {}).get('list_name', '')
                
                # Skip if list should be ignored
                if self._should_ignore_list(candidate, list_name):
                    logger.info(f"Skipping list {candidate} as it is in the ignore list or contains 'MLM'")
                    continue
                
                if (candidate not in self.list_manager.used_list_ids and 
                    self.portal_interface.verify_list_performance(candidate, campaign_id, self.metrics_history, self.thresholds)):
                    logger.info(f"Selected low-contact list {candidate} as replacement")
                    return candidate
            
            # Priority 3: Lists from user-provided queue
            while self.list_manager.list_ids:
                candidate = self.list_manager.list_ids.pop(0)
                # Skip if list is active in current metrics
                if candidate in current_metrics and current_metrics[candidate].get('is_active', False):
                    logger.info(f"Skipping list {candidate} as it is currently active")
                    continue
                
                # Get list name from metrics if available
                list_name = current_metrics.get(candidate, {}).get('list_name', '')
                
                # Skip if list should be ignored
                if self._should_ignore_list(candidate, list_name):
                    logger.info(f"Skipping list {candidate} as it is in the ignore list or contains 'MLM'")
                    continue
                
                if (candidate not in self.list_manager.used_list_ids and 
                    self.portal_interface.verify_list_performance(candidate, campaign_id, self.metrics_history, self.thresholds)):
                    logger.info(f"Selected fresh list {candidate} from user-provided queue as replacement")
                    return candidate
            
            logger.info("No suitable inactive replacement lists found in any priority category")
            return None
            
        except Exception as e:
            logger.error(f"Error getting replacement list: {e}")
            logger.error("Stack trace:", exc_info=True)
            return None

    def _handle_failed_change(self, list_id: str, high_conv_lists: List[str], low_contact_lists: List[str]):
        """Handle a failed list change by returning the list to appropriate queue"""
        if list_id in self.list_manager.used_list_ids:
            high_conv_lists.insert(0, list_id)
        elif list_id in low_contact_lists:
            low_contact_lists.insert(0, list_id)
        else:
            self.list_manager.list_ids.insert(0, list_id)

def select_server() -> str:
    """Interactive server selection"""
    print("\nAvailable Servers:")
    print("=================")
    servers = {
        "5": "OSD Server (IB5)",
        "6": "GMB Server (IB6)",
        "7": "OSD Server (IB7)",
        "A": "GMB Server (IBA)",
        "10": "OSD Server (I10)",
        "11": "OSD Server (I11)"
    }
    
    for server_id, description in servers.items():
        print(f"{server_id}: {description}")
    
    while True:
        choice = input("\nSelect server (5/6/7/A/10/11) [5]: ").strip().upper() or "5"
        if choice in servers:
            print(f"\nSelected: {servers[choice]}")
            return choice
        print("Invalid selection. Please try again.")

def load_server_config(server_id: str) -> Dict:
    """Load server-specific configuration from file"""
    try:
        # Handle both IB and I format servers
        server_prefix = "IB" if server_id in ["5", "6", "7", "A"] else "I"
        config_file = f"{server_prefix}{server_id}_CONFIG.txt"
        thresholds = {}
        if os.path.exists(config_file):
            logger.info(f"Loading configuration from {config_file}")
            with open(config_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.split('#', 1)[0].strip()  # Remove comments
                        try:
                            thresholds[key] = float(value) if '.' in value else int(value)
                        except ValueError as e:
                            logger.error(f"Error converting threshold value: {e}")
                            raise
            logger.info(f"Loaded thresholds: {thresholds}")
        return thresholds
    except Exception as e:
        logger.error(f"Error loading server configuration: {e}")
        return {}

def load_ignore_list(server_id: str) -> List[str]:
    """Load ignore list for the server"""
    try:
        # Handle both IB and I format servers
        server_prefix = "IB" if server_id in ["5", "6", "7", "A"] else "I"
        ignore_file = f"{server_prefix}{server_id}_IGNORE.txt"
        ignore_list = []
        if os.path.exists(ignore_file):
            with open(ignore_file, 'r') as file:
                for line in file:
                    list_id = line.strip()
                    if list_id:
                        ignore_list.append(list_id)
            logger.info(f"Loaded {len(ignore_list)} lists from ignore file")
        return ignore_list
    except Exception as e:
        logger.error(f"Error loading ignore list: {e}")
        return []

if __name__ == "__main__":
    portal = None
    try:
        # Load credentials if available
        stored_creds, portal_url, agent_prefixes = load_credentials()
        logger.info("Initial agent_prefixes from credentials: %s", agent_prefixes)
        
        # Interactive server selection
        server_id = select_server()
        
        # Get list IDs if any
        list_ids = get_list_ids()
        
        # Get credentials - either from file or user input
        if stored_creds and server_id in stored_creds:
            print("\nUsing stored credentials.")
            creds = stored_creds[server_id]
            # Always use DEFAULT_AGENT_PREFIXES to ensure correct configuration
            agent_prefixes = DEFAULT_AGENT_PREFIXES
            logger.info("Using DEFAULT_AGENT_PREFIXES: %s", agent_prefixes)
        else:
            print("\nNo stored credentials found for this server.")
            creds = get_user_credentials(server_id)
            agent_prefixes = DEFAULT_AGENT_PREFIXES
            logger.info("Using DEFAULT_AGENT_PREFIXES: %s", agent_prefixes)
        
        # Create configuration
        config = get_server_config(server_id, creds, list_ids, portal_url)
        
        # Display configuration
        server_config = config["server_configs"][server_id]
        print(f"\nConfiguration for server {server_id}:")
        print("=" * 40)
        print(f"Type: {server_config.server_type.value}")
        print(f"Campaigns: {', '.join(server_config.campaign_ids.values())}")
        print(f"Username: {server_config.username}")
        print(f"Using stored credentials: {'Yes' if stored_creds else 'No'}")
        
        if server_config.list_ids:
            print(f"Processing lists: {', '.join(server_config.list_ids)}")
        else:
            print("Processing all lists")
        
        print("\nThresholds:")
        print(f"  Conversion Rate: {config['thresholds'].conversion_rate}")
        print(f"  Contact Count: {config['thresholds'].contact_count}")
        print(f"  Contact Rate: {config['thresholds'].contact_rate}")
        print(f"  Rest Time: {config['thresholds'].rest_time}s")
        
        print("\nPress Ctrl+C to stop the balancer at any time.")
        input("\nPress Enter to continue...")
        
        # Create components
        portal = WebPortalInterface(config["portal_url"])
        analyzer = StandardPerformanceAnalyzer(config["thresholds"], config["server_configs"][server_id].server_type)
        verifier = AgentVerifier(agent_prefixes)
        list_manager = ListManager(
            analyzer, 
            verifier, 
            config["thresholds"],
            list_ids=server_config.list_ids
        )
        list_manager.ignore_list = load_ignore_list(server_id)
        
        # Create and start balancer
        balancer = TeleseroBalancer(
            config["server_configs"][server_id],
            portal,
            list_manager
        )
        
        balancer.start()
        
    except KeyboardInterrupt:
        print("\n")
        logger.info("Balancer stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error("Stack trace:", exc_info=True)
        sys.exit(1)
    finally:
        if portal:
            portal.driver.quit() 