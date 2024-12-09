import time
import math
import socket
import numpy as np
from collections import deque
from OpenGL.GL import *
from OpenGL.GLUT import *
from eye_widget import EyeWidget
from live_config import LiveConfig
from pointcloud_drawing_utils import fill_divider
from detection_data import DetectionData
import random 
import math

live_config = LiveConfig.get_instance()

# Initialize global variables
prev_movement_id = None
x_position_history = deque(maxlen=live_config.stable_x_thres)
y_position_history = deque(maxlen=live_config.stable_y_thres)
depth_history = deque(maxlen=live_config.stable_z_thres)

# Stores the last known stable values
stable_x_pos = None
stable_y_pos = None
stable_z_pos = None
x_direction_threshold = 5  # Threshold for detecting directional changes in x

current_direction = None               # Tracks the current movement direction ('left' or 'right')
opposite_direction_counter = 0         # Counter for consecutive movements in the opposite direction
forced_opposite_direction_count = 0    # Number of frames to move in the forced opposite direction
original_position = None               # Position to return to after forced opposite movement
direction_change_threshold = 5         # Threshold of frames before triggering forced opposite direction
forced_opposite_direction_duration = 10  # Duration for the forced opposite direction movement
jump_probability = 0.3                 # Probability of a jump occurring when forced opposite starts

def update_deque_maxlen():
    """Update deque lengths if LiveConfig threshold values have changed."""
    global x_position_history, y_position_history, depth_history
    if x_position_history.maxlen != live_config.stable_x_thres:
        x_position_history = deque(x_position_history, maxlen=live_config.stable_x_thres)
    if y_position_history.maxlen != live_config.stable_y_thres:
        y_position_history = deque(y_position_history, maxlen=live_config.stable_y_thres)
    if depth_history.maxlen != live_config.stable_z_thres:
        depth_history = deque(depth_history, maxlen=live_config.stable_z_thres)

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
    detection_data = DetectionData()
    global prev_movement_id, depth_history, y_position_history, x_position_history
    global stable_x_pos, stable_y_pos, stable_z_pos
    # Update deque lengths if thresholds have changed
    update_deque_maxlen()

    movement_id = detection_data.active_movement_id

    x_pos = find_x_divider_index(point)
    y_pos = get_y_position(point, detection_data)
    z_pos = get_z_position(point)

    if movement_id == prev_movement_id:
        # Apply hysteresis for x, y, and z positions if the same person
        stable_x_pos = apply_x_hysteresis(x_position_history, x_pos, stable_x_pos)
        stable_y_pos = apply_hysteresis(y_position_history, y_pos, stable_y_pos, live_config.stable_y_thres)
        stable_z_pos = apply_hysteresis(depth_history, z_pos, stable_z_pos, live_config.stable_z_thres)
    else:
        # Reset history and update stable positions for a new movement ID
        x_position_history.clear()
        y_position_history.clear()
        depth_history.clear()
        stable_x_pos = x_pos
        stable_y_pos = y_pos
        stable_z_pos = z_pos
        prev_movement_id = movement_id

    # if stable_x_pos and stable_y_pos and stable_z_pos:
    filename = f"bt_{stable_x_pos}_{stable_z_pos}{stable_y_pos}o.jpg"
    send_filename_to_server(filename)

# Global variables for tracking direction changes
current_direction = None  # 'left' or 'right'
opposite_direction_counter = 0
direction_change_threshold = random.randint(5, 10)  # Randomized threshold between 5 and 10
forced_opposite_direction_count = 0
forced_opposite_direction_duration = 2  # Initial forced opposite duration
jump_probability = 0.8  # 80% probability to start a few steps further

# Variable to remember the original position before the forced movement
original_position = None

def clamp(value, min_val, max_val):
    """Helper function to clamp a value within a specified range."""
    return max(min(value, max_val), min_val)

def apply_x_hysteresis(history, new_value, stable_value):
    global current_direction, opposite_direction_counter
    global forced_opposite_direction_count, original_position
    global direction_change_threshold, forced_opposite_direction_duration

    # Append new x position to the history
    history.append(new_value)

    # Initialize stable_value if it's None
    if stable_value is None:
        stable_value = new_value
        return stable_value

    # Calculate the difference between the new value and the stable value
    delta = new_value - stable_value

    # Determine the new direction based on delta
    if delta > 0:
        new_direction = 'right'
    elif delta < 0:
        new_direction = 'left'
    else:
        # No significant movement detected
        return stable_value

    if current_direction is None:
        current_direction = new_direction
        stable_value = new_value
        opposite_direction_counter = 0
    elif new_direction == current_direction:
        stable_value = new_value
        opposite_direction_counter += 1
    else:
        opposite_direction_counter = 0
        current_direction = new_direction
        stable_value = new_value

    return stable_value

def apply_hysteresis(history, new_value, stable_value, threshold):
    """Standard hysteresis for y and z positions."""
    history.append(new_value)
    
    if len(history) == history.maxlen and all(v == new_value for v in list(history)[-threshold:]):
        stable_value = new_value

    return stable_value

def find_x_divider_index(point, center_x=0, height=2.0, depth=30.0):
    live_config = LiveConfig.get_instance()  # Access the live configuration

    x, y, z = point
    delta_x = x - center_x
    delta_z = z - live_config.camera_z
    angle_to_point = math.degrees(math.atan2(delta_x, -delta_z))
    
    x_divider_angle = live_config.x_divider_angle
    num_divisions = live_config.num_divisions  # Total number of divider planes

    # Define angles across a full 180° span from -90° to +90°
    total_angle_span = x_divider_angle
    divider_angles = [-total_angle_span / 2 + i * (total_angle_span / num_divisions) for i in range(num_divisions + 1)]

    # Identify the index of the divider gap corresponding to the angle
    for i in range(len(divider_angles) - 1):
        if divider_angles[i] <= angle_to_point < divider_angles[i + 1]:
            gap_index = i
            break
    else:
        gap_index = len(divider_angles) - 2  # Default to the last gap if no match is found

    # Call fill_divider for the identified gap index to fill it
    fill_divider(gap_index, height=height, depth=depth, center_x=center_x)
    return gap_index

def get_y_position(point, detection_data, camera_y=0):
    import math

    # Unpack point coordinates
    x, y, z = point

    # Access the LiveConfig instance
    live_config = LiveConfig.get_instance()

    # Use dividers for person movement
    y_top_divider = live_config.y_top_divider
    y_bottom_divider = live_config.y_bottom_divider
    y_top_divider_angle = live_config.y_top_divider_angle
    y_bottom_divider_angle = live_config.y_bottom_divider_angle


    # Convert angles from degrees to radians
    angle_top_rad = math.radians(y_top_divider_angle)
    angle_bottom_rad = math.radians(y_bottom_divider_angle)

    # Calculate normal vectors for the planes
    cos_theta_top = math.cos(angle_top_rad)
    sin_theta_top = math.sin(angle_top_rad)
    cos_theta_bottom = math.cos(angle_bottom_rad)
    sin_theta_bottom = math.sin(angle_bottom_rad)

    # Plane positions relative to the camera
    y0_top = camera_y + y_top_divider
    y0_bottom = camera_y - y_bottom_divider

    # Compute signed distances from the point to the top and bottom planes
    D_top = cos_theta_top * (y - y0_top) + sin_theta_top * z
    D_bottom = cos_theta_bottom * (y - y0_bottom) + sin_theta_bottom * z

    # Determine the position relative to the planes
    if D_top > 0:
        return 'u'  # Above the top plane
    elif D_bottom < 0:
        return 'd'  # Below the bottom plane
    else:
        return 's'  # Between the planes

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
    return 'c'
