"""
Backend Preset Listener Service for receiving and applying preset configurations.

This module provides a service that listens for preset configuration updates sent from
the frontend PresetManager and applies them to the backend LiveConfig singleton.

The service runs in a separate thread and handles UDP socket communication for
receiving preset values.

Example preset message format:
{
    "backend": {
        "headpoint_smoothing": 0.5
    }
}
"""

import socket
import json
import logging
from typing import Optional, Dict, Any
from PyQt5.QtCore import QThread, pyqtSignal
from live_config import LiveConfig

class PresetListenerService(QThread):
    """
    Service for listening to and applying preset configuration updates.
    
    This class runs in its own thread and listens for UDP messages containing
    preset configuration values. When received, it validates and applies the
    updates to the LiveConfig singleton.
    
    Attributes:
        value_received (pyqtSignal): Signal emitted when new preset values arrive
        running (bool): Flag to control the listener loop
        port (int): Port to listen on
        live_config (LiveConfig): Reference to the LiveConfig singleton
    """
    
    # Signal emitted when a preset value is received
    backend_value_received = pyqtSignal(str, float)
    frontend_value_received = pyqtSignal(str, float)
    
    def __init__(self, port: int = 12346):
        """
        Initialize the preset listener service.
        
        Args:
            port (int): UDP port to listen on for preset messages
        """
        super().__init__()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        # Initialize service properties
        self.port = port
        self.running = True
        self.live_config = LiveConfig.get_instance()
        
        # Initialize socket
        self._init_socket()
        
    def _init_socket(self):
        """Initialize UDP socket with error handling."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('localhost', self.port))
            self.socket.settimeout(0.1)  # Allow checking stop flag
            self.logger.info(f"Successfully bound to port {self.port}")
            print(f"Successfully bound to port {self.port}")
            
        except Exception as e:
            self.logger.error(f"Error initializing socket: {e}")
            raise
            
    def run(self):
        """
        Main listener loop.
        
        Continuously listens for UDP messages containing preset values and
        processes them when received.
        """
        self.logger.info("PresetListenerService started")
        
        while self.running:
            try:
                # Receive and decode message
                data, _ = self.socket.recvfrom(1024)
                message = json.loads(data.decode())
                
                # Process backend preset values if present
                print(message)
                if message and message.get("category") == "backend":
                    self._process_backend_values(message)

                elif message and message.get("category") == "frontend":
                    self._process_frontend_values(message)
                    
            except socket.timeout:
                continue
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding message: {e}")
            except Exception as e:
                self.logger.error(f"Error receiving data: {e}")
                
    def _process_backend_values(self, backend_values: Dict[str, Any]):
        """
        Process and apply backend preset values.
        
        Args:
            backend_values (Dict[str, Any]): Dictionary of backend values to apply
        """
        # iterate over the dictionary and print the key and value
        variable = backend_values.get("variable")
        value = backend_values.get("value")

        try:
            if hasattr(self.live_config, variable):
                # Update LiveConfig value
                setattr(self.live_config, variable, value)
                # Emit signal for any listeners
                self.backend_value_received.emit(variable, value)
                self.logger.debug(f"Applied preset value: {variable}={value}")
                print(f"Applied preset value: {variable}={value}")
            else:
                self.logger.warning(f"Unknown backend setting: {variable}")
        
        except Exception as e:
            self.logger.error(f"Error applying preset value {variable}: {e}")

    def _process_frontend_values(self, frontend_values: Dict[str, Any]):
        """
        Process frontend preset values to update GUI sliders.
        
        Args:
            frontend_values (Dict[str, Any]): Dictionary containing:
                - variable: Name of the frontend setting to update 
                - value: New value to apply
        """
        try:
            # Get the variable name and value
            variable = frontend_values.get("variable")
            value = frontend_values.get("value")
            
            # Basic validation
            if variable is None or value is None:
                self.logger.error("Missing variable or value in frontend preset")
                return
                
            # Log what we received
            print(f"Received frontend preset: {variable} = {value}")
            
            # Emit signal with the received values
            self.frontend_value_received.emit(variable, value)
            
        except Exception as e:
            self.logger.error(f"Error in _process_frontend_values: {e}")
                
    def stop(self):
        """
        Stop the listener service cleanly.
        
        Ensures socket is properly closed and thread is terminated.
        """
        self.logger.info("Stopping PresetListenerService")
        self.running = False
        self.wait()  # Wait for thread to finish
        self.socket.close()
        self.logger.info("PresetListenerService stopped")