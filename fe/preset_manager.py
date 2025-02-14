"""
Preset Manager for handling backend configuration presets in the display system.

This module provides functionality for loading and applying backend configuration presets
from JSON files through socket communication.

Example JSON preset format:
{
    "backend": {
        "headpoint_smoothing": 0.7
    }
}
"""

import json
import socket
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class PresetManager:
    """
    Manages loading and applying backend configuration presets.
    
    This class handles reading preset configurations from JSON files and transmitting
    the settings through socket communication.
    
    Attributes:
        logger (logging.Logger): Logger instance for the class
        backend_port (int): Port number for backend socket communication
    """
    
    def __init__(self, backend_port: int = 12346):
        """
        Initialize PresetManager with specified port.
        
        Args:
            backend_port (int): Port number for backend communication
        """
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        # Initialize port
        self.backend_port = backend_port
        
        # Initialize socket
        self._init_socket()

        self.auto_switch_interval_low = None
        self.auto_switch_interval_high = None
        
    def _init_socket(self):
        """Initialize UDP socket for communication."""
        try:
            # Create backend socket
            self.backend_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.backend_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
        except socket.error as e:
            self.logger.error(f"Failed to initialize socket: {e}")
            raise
            
    def load_preset(self, preset_path: str) -> Optional[Dict[str, Any]]:
        """
        Load a preset configuration from a JSON file.
        
        Args:
            preset_path (str): Path to the preset JSON file
            
        Returns:
            Optional[Dict[str, Any]]: Loaded preset data or None if loading fails
            
        Raises:
            FileNotFoundError: If preset file doesn't exist
            json.JSONDecodeError: If preset file contains invalid JSON
        """
        try:
            preset_file = Path(preset_path)
            if not preset_file.exists():
                self.logger.error(f"Preset file not found: {preset_path}")
                return None
                
            with open(preset_file, 'r') as f:
                preset_data = json.load(f)
                
            self.logger.info(f"Successfully loaded preset: {preset_path}")
            return preset_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in preset file {preset_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading preset {preset_path}: {e}")
            raise
            
    def apply_preset(self, preset_data: Dict[str, Any]) -> bool:
        """
        Apply a loaded preset configuration by sending backend values through socket.
        
        Args:
            preset_data (Dict[str, Any]): Preset configuration data
            
        Returns:
            bool: True if preset was applied successfully, False otherwise
        """
        success = True
        
        try:
            # Handle backend settings
            if "backend" in preset_data:
                for key, value in preset_data["backend"].items():
                    if not self._send_backend_value(key, value):
                        success = False

            if "frontend" in preset_data:
                for key, value in preset_data["frontend"].items():
                    if not self._send_frontend_value(key, value):
                        success = False
                        
            if success:
                self.logger.info("Successfully applied preset")
            else:
                self.logger.warning("Some preset values failed to apply")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error applying preset: {e}")
            return False
            
    def _send_backend_value(self, variable: str, value: Any) -> bool:
        """
        Send a value to the backend through UDP socket.
        
        Args:
            variable (str): Name of the variable to update
            value (Any): Value to set
            
        Returns:
            bool: True if value was sent successfully, False otherwise
        """
        try:
            message = {
                "category": "backend",
                "variable": variable,
                "value": value
            }
            
            print(f"Sending backend value: {variable}={value} to port {self.backend_port}")
            self.backend_socket.sendto(
                json.dumps(message).encode(),
                ('localhost', self.backend_port)
            )
            
            self.logger.debug(f"Sent backend value: {variable}={value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending backend value {variable}: {e}")
            return False
        
    def _send_frontend_value(self, variable: str, value: Any) -> bool:
        """
        Send a value to the frontend through UDP socket.
        
        Args:
            variable (str): Name of the variable to update
            value (Any): Value to set
            
        Returns:
            bool: True if value was sent successfully, False otherwise
        """
        try:
            if variable == "auto_switch_interval_low":
                self.auto_switch_interval_low = value
                return True
            if variable == "auto_switch_interval_high":
                self.auto_switch_interval_high = value
                return True

            message = {
                "category": "frontend",
                "variable": variable,
                "value": value
            }
            
            print(f"Sending frontend value: {variable}={value} to port {self.backend_port}")
            self.backend_socket.sendto(
                json.dumps(message).encode(),
                ('localhost', self.backend_port)
            )
            
            self.logger.debug(f"Sent frontend value: {variable}={value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending frontend value {variable}: {e}")
            return False
        


        
            
    def close(self):
        """Clean up resources by closing socket."""
        try:
            self.backend_socket.close()
            self.logger.info("Closed socket")
        except Exception as e:
            self.logger.error(f"Error closing socket: {e}")

    def __enter__(self):
        """Enable context manager support."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure proper cleanup when used as context manager."""
        self.close()