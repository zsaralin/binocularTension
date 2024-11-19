import json
import socket

def apply_config_to_server():
    """Reads the config.json and applies the folder switch based on its version."""
    config_path = "config.json"  # Path to the config file
    try:
        # Load configuration
        with open(config_path, "r") as f:
            config = json.load(f)

        # Extract version and determine target folder
        version = config.get("version", "jade").lower()
        if version not in ["jade", "gab"]:
            print(f"Invalid folder version in config: {version}. Defaulting to 'jade'.")
            version = "jade"

        switch_folder_on_server(version)

    except FileNotFoundError:
        print(f"Config file not found at {config_path}. Using default settings.")
    except json.JSONDecodeError:
        print(f"Error decoding config file at {config_path}. Using default settings.")

def switch_folder_on_server(folder_name):
    """Sends a folder switch command to the server if it's running."""
    host = "localhost"  # Adjust if server is on a different host
    port = 65432        # Port used by the server

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            switch_command = f"switch:{folder_name}"
            client_socket.sendall(switch_command.encode())
            print(f"Sent folder switch command: {switch_command}")
    except ConnectionRefusedError:
        print("Server is not running. Unable to send folder switch command.")