"""Configuration classes for browser drivers."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class DriverConfig:
    """Configuration for browser drivers.
    
    Attributes:
        executable_path: Path to the browser driver executable
        service_log_path: Path to the log file for the driver service
        port: Port to use for the driver service
        service_args: Additional arguments to pass to the driver service
        env: Environment variables to set for the driver process
    """
    executable_path: Optional[str] = None
    service_log_path: Optional[str] = None
    port: int = 0  # 0 means use any free port
    service_args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary.
        
        Returns:
            Dictionary containing the configuration
        """
        return {
            'executable_path': self.executable_path,
            'service_log_path': self.service_log_path,
            'port': self.port,
            'service_args': self.service_args.copy(),
            'env': self.env.copy()
        }


# Default configuration for drivers
DEFAULT_DRIVER_CONFIG = DriverConfig()
