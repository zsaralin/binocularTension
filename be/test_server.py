"""Simple test server for frontend slider updates."""

import socket
import json

def run_test_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('localhost', 12345))
    print("Test server listening...")
    
    try:
        while True:
            data, addr = server_socket.recvfrom(1024)
            message = json.loads(data.decode())
            var_name = message["variable"]
            value = message["value"]
            print(f"{var_name}: {value}")
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    run_test_server()