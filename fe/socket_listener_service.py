"""
Socket listener service for handling frontend settings updates and commands.
"""

import socket
import json
from PyQt5.QtCore import QThread, pyqtSignal
from display_live_config import DisplayLiveConfig

class SocketListenerService(QThread):
    """
    Persistent socket listener service for the application.
    
    Attributes:
        value_received (pyqtSignal): Signal emitted when new values arrive
        running (bool): Flag to control the listener loop
        port (int): Port to listen on
    """
    
    value_received = pyqtSignal(str, float)  # Emits (variable_name, value)
    
    def __init__(self, port=12345):
        """Initialize the socket listener service."""
        super().__init__()
        print("Initializing SocketListenerService...")
        self.port = port
        self.running = True
        self.live_config = DisplayLiveConfig.get_instance()
        self._init_socket()

    def _init_socket(self):
        """Initialize UDP socket with error handling."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('localhost', self.port))
            self.socket.settimeout(0.1)  # Allow checking stop flag
            print(f"Successfully bound to port {self.port}")
        except Exception as e:
            print(f"Error initializing socket: {e}")
            raise

    def run(self):
        """Main listener loop."""
        print("SocketListenerService started...")
        while self.running:
            try:
                data, _ = self.socket.recvfrom(1024)
                message = json.loads(data.decode())
                
                # Check if this is a save command
                if 'command' in message and message['command'] == 'save':
                    print("Save command received, saving frontend config...")
                    self.live_config.save_config()
                    continue
                    
                # Otherwise handle normal value updates
                if 'variable' in message and 'value' in message:
                    try:
                        value = float(message['value'])
                        self.value_received.emit(
                            message["variable"],
                            value
                        )
                    except (ValueError, TypeError) as e:
                        print(f"Error processing value {message['value']}: {e}")
                else:
                    print(f"Invalid message format: {message}")
                    
            except socket.timeout:
                continue
            except json.JSONDecodeError as e:
                print(f"Error decoding message: {e}")
            except Exception as e:
                print(f"Error receiving data: {e}")
                
    def stop(self):
        """Stop the listener service cleanly."""
        print("Stopping SocketListenerService...")
        self.running = False
        self.wait()
        self.socket.close()
        print("SocketListenerService stopped")