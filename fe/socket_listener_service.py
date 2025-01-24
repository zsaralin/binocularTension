"""
Socket listener service for handling frontend settings updates.
Maintains a persistent UDP socket connection throughout application lifetime.
"""

import socket
import json
from PyQt5.QtCore import QThread, pyqtSignal

class SocketListenerService(QThread):
    """
    Persistent socket listener service for the application.
    
    This service maintains a UDP socket connection and emits signals
    when frontend settings updates are received.
    
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
                self.value_received.emit(
                    message["variable"],
                    message["value"]
                )
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error receiving data: {e}")
                
    def stop(self):
        """Stop the listener service cleanly."""
        print("Stopping SocketListenerService...")
        self.running = False
        self.wait()
        self.socket.close()
        print("SocketListenerService stopped")