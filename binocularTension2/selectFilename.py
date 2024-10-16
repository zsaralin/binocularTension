import socket
def send_filename_to_server(filename):
    """Send the generated filename to the Pygame server."""
    host = 'localhost'
    port = 65432

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            client_socket.sendall(filename.encode())
            print(f"Sent filename: {filename}")
    except ConnectionRefusedError:
        print("Failed to connect to the server. Is main.py running?")

def get_image(x, y, depth, image_width, image_height):
    section = min(int((x / image_width) * 42), 41)  # Clamp to 41 max
    distance = 'c' if depth <= 4 else 'f'  # 'c' for close, 'f' for far

    if y < image_height / 3:
        position = 'u'  # Upper third
    elif y > (2 * image_height) / 3:
        position = 'd'  # Lower third
    else:
        position = 's'  # Middle third

    filename = f"bt_{section}_{distance}{position}o.png"

    # Send the filename to main.py
    send_filename_to_server(filename)
