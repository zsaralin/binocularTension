import math 
import socket
import time
from live_config import LiveConfig
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *

# Access the LiveConfig instance
live_config = LiveConfig.get_instance()

def send_filename_to_server(filename):
    """Send the generated filename to the Pygame server."""
    host = 'localhost'
    port = 65432

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            client_socket.sendall(filename.encode())
    except ConnectionRefusedError:
        print("Failed to connect to the server. Is main.py running?")
class ThresholdStabilizer:
    def __init__(self, stabilization_time=0.01):
        # Store the last observed values for each tracked key
        self.last_values = {
            "y_position": None,
            "section": None,
            "distance": None
        }
        self.last_stabilized_time = {
            "y_position": 0,
            "section": 0,
            "distance": 0
        }
        self.stabilization_time = stabilization_time

    def stabilize(self, new_value, key):
        """Generic stabilization method based on value stability over time."""
        current_time = time.time()

        # Check if the value has changed from the last stable value
        if self.last_values[key] != new_value:
            # Value changed, reset timer and update the last observed value
            self.last_values[key] = new_value
            self.last_stabilized_time[key] = current_time
            return None  # Return None until value is stable for required time

        # If the value remains unchanged, check the stabilization time
        if current_time - self.last_stabilized_time[key] >= self.stabilization_time:
            return new_value  # Value has stabilized
        else:
            return None  # Continue waiting for stabilization

    def stabilize_y(self, new_value):
        return self.stabilize(new_value, "y_position")

    def stabilize_section(self, new_value):
        return self.stabilize(new_value, "section")

    def stabilize_distance(self, new_value):
        return self.stabilize(new_value, "distance")

# Initialize stabilizer with stabilization time of 1 second
stabilizer = ThresholdStabilizer()

# Modify your get_image function
def get_image(point, image_width, image_height):
    x_pos = find_x_divider_index(point)
    # x_pos = stabilizer.stabilize_section(x_pos)

    z_pos = get_z_position(point)
    # z_pos = stabilizer.stabilize_distance(z_pos)

    y_pos = get_y_position(point)
    # y_pos = stabilizer.stabilize_y(y_pos)

    # if x_pos and z_pos and y_pos:
    filename = f"bt_{x_pos}_{z_pos}{y_pos}o.png"
    send_filename_to_server(filename)

def find_x_divider_index(point, center_x=0, camera_z=0, height=2.0, depth=30.0):
    x, y, z = point
    delta_x = x - center_x
    delta_z = z - camera_z
    angle_to_point = math.degrees(math.atan2(delta_x, -delta_z))  # Invert z to align with depth direction
    x_divider_angle = live_config.x_divider_angle
    
    divider_angles = [i * (2 * x_divider_angle / 41) - x_divider_angle for i in range(42)]
    closest_divider_angle = min(divider_angles, key=lambda a: abs(a - angle_to_point))
    divider_index = divider_angles.index(closest_divider_angle)
    return divider_index

def get_y_position(point, camera_y=0):
    x, y, z = point
    live_config = LiveConfig.get_instance()
    y_top_divider = live_config.y_top_divider
    y_bottom_divider = live_config.y_bottom_divider

    top_y_position = camera_y + y_top_divider
    bottom_y_position = camera_y - y_bottom_divider
    
    if y > top_y_position:
        return 'u'  # Above top divider
    elif y < bottom_y_position:
        return 'd'  # Below bottom divider
    else:
        return 's'  # Between dividers

def define_depth_plane_segments(camera_z=0, segments=20):
    """Define the depth plane as a set of triangles."""
    live_config = LiveConfig.get_instance()
    depth_offset = -live_config.z_divider
    curve_radius = live_config.z_divider_curve
    plane_z = camera_z + depth_offset

    angle_span = math.pi if curve_radius != 0 else 0  # 180 degrees if curved
    start_angle = -angle_span / 2
    triangles = []

    for i in range(segments):
        angle1 = start_angle + (i * angle_span / segments)
        angle2 = start_angle + ((i + 1) * angle_span / segments)

        if curve_radius != 0:
            x1 = curve_radius * math.sin(angle1)
            z1 = plane_z - curve_radius * math.cos(angle1)
            x2 = curve_radius * math.sin(angle2)
            z2 = plane_z - curve_radius * math.cos(angle2)
        else:
            x1, z1 = (i - segments / 2) * (2000.0 / segments), plane_z
            x2, z2 = ((i + 1) - segments / 2) * (2000.0 / segments), plane_z

        triangle1 = [(x1, -1000, z1), (x2, -1000, z2), (x2, 1000, z2)]
        triangle2 = [(x1, -1000, z1), (x2, 1000, z2), (x1, 1000, z1)]
        triangles.extend([triangle1, triangle2])

    return triangles

def point_behind_plane(point, triangles):
    """Check if a point is behind the mesh defined by the plane."""
    def signed_distance_to_triangle(point, triangle):
        p = np.array(point)
        v0, v1, v2 = np.array(triangle[0]), np.array(triangle[1]), np.array(triangle[2])
        normal = np.cross(v1 - v0, v2 - v0)
        normal /= np.linalg.norm(normal)
        distance = np.dot(normal, p - v0)
        return distance < 0

    for triangle in triangles:
        if signed_distance_to_triangle(point, triangle):
            return True
    return False

def get_z_position(point, camera_z=0):
    """Check if point is in front or behind a curved plane."""
    live_config = LiveConfig.get_instance()
    triangles = define_depth_plane_segments(camera_z)
    return 'f' if point_behind_plane(point, triangles) else 'c'
