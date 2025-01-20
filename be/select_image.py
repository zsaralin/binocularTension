import math
import socket
from collections import deque
from OpenGL.GL import *
from OpenGL.GLUT import *
from eye_widget import EyeWidget
from live_config import LiveConfig
from pointcloud_drawing_utils import fill_divider
from detection_data import DetectionData
import random 

# Singleton instance of live configuration
live_config = LiveConfig.get_instance()

# Initialize global variables
x_position_history = deque(maxlen=live_config.stable_x_thres)
y_position_history = deque(maxlen=live_config.stable_y_thres)
prev_movement_id = None
stable_x_pos = None
stable_y_pos = None

# Function to update deque lengths dynamically
def update_deque_maxlen():
    global x_position_history, y_position_history
    if x_position_history.maxlen != live_config.stable_x_thres:
        x_position_history = deque(x_position_history, maxlen=live_config.stable_x_thres)
    if y_position_history.maxlen != live_config.stable_y_thres:
        y_position_history = deque(y_position_history, maxlen=live_config.stable_y_thres)

def send_filename_to_server(filename, is_new_movement):
    eye_widget = EyeWidget()
    eye_widget.load_image(filename)

    host = 'localhost'
    port = 65432

    movement_status = "new" if is_new_movement else "old"
    message = f"{filename}|{movement_status}"
    print(filename)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            client_socket.sendall(message.encode())
    except ConnectionRefusedError:
        print("Failed to connect to the server. Is main.py running?")

def get_image(point, image_width, image_height):
    detection_data = DetectionData()
    global prev_movement_id, stable_x_pos, stable_y_pos

    update_deque_maxlen()

    movement_id = detection_data.active_movement_id
    x_pos = find_x_divider_index(point)
    y_pos = get_y_position(point, detection_data)

    is_new_movement = movement_id != prev_movement_id

    if is_new_movement:
        print("🔹 New movement detected! Resetting stabilization.")
        stable_x_pos, stable_y_pos = x_pos, y_pos  # Immediately update
    else:
        stable_x_pos = apply_hysteresis(x_position_history, x_pos, stable_x_pos, live_config.stable_x_thres)
        stable_y_pos = apply_hysteresis(y_position_history, y_pos, stable_y_pos, live_config.stable_y_thres)

    prev_movement_id = movement_id  # Update last movement ID

    filename = f"bt_{stable_x_pos}_c{stable_y_pos}o.jpg"
    send_filename_to_server(filename, is_new_movement)

# Hysteresis function for stable value calculation
def apply_hysteresis(history, new_value, stable_value, threshold):
    history.append(new_value)
    if len(history) == history.maxlen and all(v == new_value for v in list(history)[-threshold:]):
        stable_value = new_value
    return stable_value

# Function to find the X divider index based on the angle
def find_x_divider_index(point, center_x=0):
    x, _, z = point
    delta_x = x - center_x
    delta_z = z - live_config.camera_z
    angle_to_point = math.degrees(math.atan2(delta_x, -delta_z))

    x_divider_angle = live_config.x_divider_angle
    num_divisions = live_config.num_divisions
    total_angle_span = x_divider_angle

    divider_angles = [-total_angle_span / 2 + i * (total_angle_span / num_divisions) for i in range(num_divisions + 1)]
    for i in range(len(divider_angles) - 1):
        if divider_angles[i] <= angle_to_point < divider_angles[i + 1]:
            gap_index = i
            break
    else:
        gap_index = len(divider_angles) - 2

    fill_divider(gap_index, height=2.0, depth=30.0, center_x=center_x)
    return gap_index

# Function to determine Y position based on dividers
def get_y_position(point, detection_data, camera_y=0):
    _, y, z = point

    y_top_divider = live_config.y_top_divider
    y_bottom_divider = live_config.y_bottom_divider
    y_top_divider_angle = math.radians(live_config.y_top_divider_angle)
    y_bottom_divider_angle = math.radians(live_config.y_bottom_divider_angle)

    y0_top = camera_y + y_top_divider
    y0_bottom = camera_y - y_bottom_divider

    D_top = math.cos(y_top_divider_angle) * (y - y0_top) + math.sin(y_top_divider_angle) * z
    D_bottom = math.cos(y_bottom_divider_angle) * (y - y0_bottom) + math.sin(y_bottom_divider_angle) * z

    if D_top > 0:
        return 'u'
    elif D_bottom < 0:
        return 'd'
    else:
        return 's'