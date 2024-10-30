import time
import math
import socket
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from eye_widget import EyeWidget
from live_config import LiveConfig
from pointcloud_drawing_utils import fill_divider
# Access the LiveConfig instance
live_config = LiveConfig.get_instance()

# Define the hysteresis-like behavior handler
class HysteresisHandler:
    def __init__(self, revert_delay=0):
        self.current_value = None
        self.previous_value = None
        self.last_update_time = time.time()
        self.revert_delay = revert_delay

    def update(self, new_value):
        current_time = time.time()

        # Update immediately if it's a new value
        if self.current_value != new_value:
            self.previous_value = self.current_value
            self.current_value = new_value
            self.last_update_time = current_time
            return self.current_value

        # Revert to previous only if no new updates within revert delay
        if current_time - self.last_update_time >= self.revert_delay:
            self.current_value = self.previous_value
            self.previous_value = None  # Prevents immediate toggle back
            return self.current_value

        # Return the current value without reverting
        return self.current_value

# Initialize handlers for x, y, z values
x_handler = HysteresisHandler()
y_handler = HysteresisHandler()
z_handler = HysteresisHandler()

def send_filename_to_server(filename):
    eye_widget = EyeWidget()
    eye_widget.load_image(filename)

    host = 'localhost'
    port = 65432

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            client_socket.sendall(filename.encode())
    except ConnectionRefusedError:
        print("Failed to connect to the server. Is main.py running?")

def get_image(point, image_width, image_height):
    x_pos = x_handler.update(find_x_divider_index(point))
    y_pos = y_handler.update(get_y_position(point))
    z_pos = z_handler.update(get_z_position(point))
    if x_pos and y_pos and z_pos: 
        filename = f"bt_{x_pos}_{z_pos}{y_pos}o.png"
        send_filename_to_server(filename)

def find_x_divider_index(point, center_x=0, camera_z=0, height=2.0, depth=30.0):
    x, y, z = point
    delta_x = x - center_x
    delta_z = z - camera_z
    angle_to_point = math.degrees(math.atan2(delta_x, -delta_z))
    x_divider_angle = live_config.x_divider_angle

    divider_angles = [i * (2 * x_divider_angle / 41) - x_divider_angle for i in range(42)]
    closest_divider_angle = min(divider_angles, key=lambda a: abs(a - angle_to_point))
    divider_index = divider_angles.index(closest_divider_angle)
    fill_divider(divider_index)
    return divider_index

def get_y_position(point, camera_y=0):
    _, y, _ = point
    y_top_divider = live_config.y_top_divider
    y_bottom_divider = live_config.y_bottom_divider

    if y > camera_y + y_top_divider:
        return 'u'
    elif y < camera_y - y_bottom_divider:
        return 'd'
    else:
        return 's'

def define_depth_plane_segments(camera_z=0, segments=20):
    depth_offset = -live_config.z_divider
    curve_radius = live_config.z_divider_curve
    plane_z = camera_z + depth_offset

    angle_span = math.pi if curve_radius != 0 else 0
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
    p = np.array(point)

    for triangle in triangles:
        v0, v1, v2 = np.array(triangle[0]), np.array(triangle[1]), np.array(triangle[2])
        normal = np.cross(v1 - v0, v2 - v0)
        normal /= np.linalg.norm(normal)
        distance = np.dot(normal, p - v0)
        if distance < 0:
            return True
    return False

def get_z_position(point, camera_z=0):
    triangles = define_depth_plane_segments(camera_z)
    return 'f' if point_behind_plane(point, triangles) else 'c'
