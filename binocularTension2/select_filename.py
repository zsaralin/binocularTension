import socket
import time

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

class ThresholdStabilizer:
    def __init__(self, required_consistency=500, stabilization_time=20.0):
        self.y_position_history = []
        self.section_history = []
        self.distance_history = []
        self.last_stabilized_time = {
            "y_position": 0,
            "section": 0,
            "distance": 0
        }
        self.required_consistency = required_consistency
        self.stabilization_time = stabilization_time

    def stabilize(self, new_value, history, key):
        """Generic stabilization method based on time difference."""
        current_time = time.time()

        # Append new value to history
        history.append(new_value)

        # Trim history to the required consistency size
        if len(history) > self.required_consistency:
            history.pop(0)

        # If all values in history are the same, we can stabilize
        if len(set(history)) == 1:
            # If enough time has passed since the last stabilization
            if current_time - self.last_stabilized_time[key] >= self.stabilization_time:
                self.last_stabilized_time[key] = current_time
                return new_value  # Stabilized value
            else:
                return history[-1]  # Keep previous stable value

        return history[-1]  # Return the last stable value

    def stabilize_y(self, new_value):
        return self.stabilize(new_value, self.y_position_history, "y_position")

    def stabilize_section(self, new_value):
        return self.stabilize(new_value, self.section_history, "section")

    def stabilize_distance(self, new_value):
        return self.stabilize(new_value, self.distance_history, "distance")

# Initialize stabilizer with stabilization time of 1 second
stabilizer = ThresholdStabilizer()

# Modify your get_image function
def get_image(x, y, depth, image_width, image_height):
    section = 41 - min(int((x / image_width) * 42), 41)  # Clamp to 41 max

    # Stabilize the x section
    section = stabilizer.stabilize_section(section)

    # Determine if the point is within the close depth
    distance = 'c' if depth <= 3 else 'f'  # 'c' for close, 'f' for far
    distance = stabilizer.stabilize_distance(distance)  # Stabilize depth

    # Determine position based on depth
    if distance == 'c':
        # Close depth: use 1/4 for upper, middle, and lower parts
        if y < image_height / 4:
            position = 'u'  # Upper quarter
        elif y > image_height / 2:
            position = 'd'  # Below half
        else:
            position = 's'  # Middle
    else:
        # Far depth: use 1/3 for top, middle, and bottom
        if y < image_height / 4:
            position = 'u'  # Upper third
        elif y > (2 * image_height) / 4:
            position = 'd'  # Lower third
        else:
            position = 's'  # Middle third

    # Stabilize y position
    position = stabilizer.stabilize_y(position)

# Only update the filename if all values have stabilized
    if (len(set(stabilizer.section_history)) == 1 and
        len(set(stabilizer.distance_history)) == 1 and
        len(set(stabilizer.y_position_history)) == 1):
        
        filename = f"bt_{section}_{distance}{position}o.png"
        send_filename_to_server(filename)
    # Send the filename to main.py
