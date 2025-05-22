"""Chrome service management.

This module provides a class for managing the ChromeDriver service.
"""
import logging
from typing import List, Optional, Union
from pathlib import Path
from selenium.webdriver.chrome.service import Service as ChromeService
from typing import Optional, Dict, Any, Union, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ChromeServiceManager:
    """Manages the ChromeDriver service lifecycle."""
    
    def __init__(
        self,
        executable_path: Optional[Union[str, Path]] = None,
        port: int = 0,
        service_args: Optional[List[str]] = None,
        log_path: Optional[Union[str, Path]] = None,
        env: Optional[dict] = None
    ) -> None:
        """Initialize the Chrome service manager.
        
        Args:
            executable_path: Path to the ChromeDriver executable.
            port: Port to run the service on. 0 means any free port.
            service_args: Additional arguments to pass to the service.
            log_path: Path to log file for ChromeDriver output.
            env: Environment variables to set for the service.
        """
        self._executable_path = str(executable_path) if executable_path else None
        self._port = port
        self._service_args = service_args or []
        self._log_path = str(log_path) if log_path else None
        self._env = env or {}
        self._service: Optional[ChromeService] = None
    
    def start(self) -> ChromeService:
        """Start the Chrome service.
        
        Returns:
            The started ChromeService instance.
            
        Raises:
            WebDriverException: If the service fails to start.
        """
        if self._service and self._service.service_url:
            logger.warning("Service is already running")
            return self._service
            
        try:
            logger.info(f"Starting Chrome service on port {self._port}")
            self._service = ChromeService(
                executable_path=self._executable_path,
                port=self._port,
                service_args=self._service_args,
                log_path=self._log_path,
                env=self._env
            )
            self._service.start()
            logger.info(f"Chrome service started at {self._service.service_url}")
            return self._service
            
        except Exception as e:
            logger.error(f"Failed to start Chrome service: {e}")
            self.stop()
            raise
    
    def stop(self) -> None:
        """Stop the Chrome service if it's running."""
        if not self._service:
            return
            
        try:
            if hasattr(self._service, 'stop'):
                self._service.stop()
            else:
                self._service.process.terminate()
                
            logger.info("Chrome service stopped")
            
        except Exception as e:
            logger.error(f"Error while stopping Chrome service: {e}")
            raise
            
        finally:
            self._service = None
    
    @property
    def service_url(self) -> Optional[str]:
        """Get the service URL if the service is running."""
        if not self._service or not hasattr(self._service, 'service_url'):
            return None
        return self._service.service_url
    
    def is_running(self) -> bool:
        """Check if the service is running."""
        return self._service is not None and self._service.service_url is not None
    
    def __enter__(self) -> 'ChromeServiceManager':
        """Context manager entry point."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit point."""
        self.stop()
    
    def __del__(self) -> None:
        """Ensure the service is stopped when the object is garbage collected."""
        self.stop()


class ChromeServiceFactory:
    """Factory for creating and managing Chrome service instances."""
    
    def __init__(self, config: Any) -> None:
        """Initialize the service factory with the given configuration.
        
        Args:
            config: Configuration object containing service settings.
        """
        self._config = config
        self._service: Optional[ChromeService] = None
    
    def create_service(self) -> ChromeService:
        """Create and return a configured ChromeService instance.
        
        Returns:
            Configured ChromeService instance.
            
        Raises:
            WebDriverException: If the service cannot be created.
        """
        service_args = self._get_service_args()
        
        self._service = ChromeService(
            executable_path=self._config.chrome_driver_path,
            service_args=service_args,
            log_path=self._config.log_path
        )
        
        return self._service
    
    def _get_service_args(self) -> List[str]:
        """Get the service arguments from the configuration.
        
        Returns:
            List of service arguments.
        """
        args = []
        
        if hasattr(self._config, 'service_args'):
            args.extend(self._config.service_args)
            
        if hasattr(self._config, 'port') and self._config.port:
            args.extend(['--port', str(self._config.port)])
            
        return args
    
    def stop_service(self) -> None:
        """Stop the Chrome service if it's running."""
        if self._service is not None:
            try:
                self._service.stop()
            except Exception as e:
                logging.warning(f"Error stopping Chrome service: {e}")
            finally:
                self._service = None
