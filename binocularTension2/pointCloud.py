import cv2
import numpy as np
import pyrealsense2 as rs
import math
from PyQt5.QtWidgets import QApplication
from ultralytics import YOLO
from collections import deque
from scipy import stats
import sys
from gui import ControlPanel
import socket

# Initialize YOLO model
model = YOLO("yolov8n.pt")
model.verbose = False  # Suppress logging

# Configure RealSense streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 60)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 60)
profile = pipeline.start(config)

# Get depth scale
depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()

# Get camera intrinsics
depth_intrinsics = profile.get_stream(rs.stream.depth).as_video_stream_profile().get_intrinsics()
color_intrinsics = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()

# Initialize PyQt5 GUI
app = QApplication(sys.argv)
control_panel = ControlPanel()
control_panel.show()

# Initialize tracked objects
tracked_objects = {}

# Movement threshold (in pixels)
movement_threshold = 5
window_size = 5  # Moving average window size

# Motion detection parameters
motion_threshold = 25  # Threshold for frame differencing
min_area = 500  # Minimum area of contours to be considered motion

# Initialize previous frame for motion detection
previous_frame = None

def get_rotation_matrix(angles):
    Rx = np.array([[1, 0, 0],
                   [0, math.cos(angles[0]), -math.sin(angles[0])],
                   [0, math.sin(angles[0]), math.cos(angles[0])]])
    Ry = np.array([[math.cos(angles[1]), 0, math.sin(angles[1])],
                   [0, 1, 0],
                   [-math.sin(angles[1]), 0, math.cos(angles[1])]])
    Rz = np.array([[math.cos(angles[2]), -math.sin(angles[2]), 0],
                   [math.sin(angles[2]), math.cos(angles[2]), 0],
                   [0, 0, 1]])
    return np.dot(Rz, np.dot(Ry, Rx))

def apply_transform(verts, rotation_matrix, translation_values):
    """Apply rotation and translation to 3D vertices."""
    transformed_verts = np.dot(verts, rotation_matrix.T) + np.array(translation_values)
    return transformed_verts

def convert_depth_pixel_to_metric_coordinate(depth, pixel_x, pixel_y, intrinsics):
    """Convert depth image pixel to metric coordinate."""
    x = (pixel_x - intrinsics.ppx) / intrinsics.fx * depth
    y = (pixel_y - intrinsics.ppy) / intrinsics.fy * depth
    z = depth
    return x, y, z

def project_to_2d(point, intrinsics):
    """Project 3D point to 2D using camera intrinsics."""
    x, y, z = point
    if z == 0:
        return None
    pixel_x = int((x / z) * intrinsics.fx + intrinsics.ppx)
    pixel_y = int((y / z) * intrinsics.fy + intrinsics.ppy)
    return pixel_x, pixel_y

def get_depth(depth_image, bbox, num_samples=100, bin_size=0.01):
    """Calculate the most representative depth within the bounding box."""
    x1, y1, x2, y2 = bbox
    xs = np.random.randint(x1, x2, num_samples)
    ys = np.random.randint(y1, y2, num_samples)
    depth_values = depth_image[ys, xs].flatten()
    valid_depths = depth_values[depth_values > 0] * depth_scale
    if len(valid_depths) == 0:
        return None
    binned_depths = np.round(valid_depths / bin_size) * bin_size
    mode_result = stats.mode(binned_depths, keepdims=True)
    if mode_result.count[0] > 1:
        return mode_result[0][0]
    else:
        return np.median(valid_depths)
def process_frame(color_image, depth_image, tracked_objects, rotation_matrix, translation_values, depth_intrinsics):
    global previous_frame
    moving_objects = []

    # Convert color image to grayscale for motion detection
    gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if previous_frame is None:
        previous_frame = gray
        return color_image, moving_objects

    # Compute the absolute difference between frames
    frame_delta = cv2.absdiff(previous_frame, gray)
    thresh = cv2.threshold(frame_delta, motion_threshold, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_mask = np.zeros_like(gray)

    for contour in contours:
        if cv2.contourArea(contour) > min_area:
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(motion_mask, (x, y), (x + w, y + h), 255, -1)

    results = model.track(color_image, persist=True, verbose=False)

    if results[0].boxes is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        ids = results[0].boxes.id.cpu().numpy() if results[0].boxes.id is not None else None

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box[:4])
            if np.any(motion_mask[y1:y2, x1:x2] > 0):
                object_id = int(ids[i]) if ids is not None else i
                midpoint = ((x1 + x2) // 2, (y1 + y2) // 2)

                depth_value = depth_image[
                    min(max(midpoint[1], 0), depth_image.shape[0] - 1),
                    min(max(midpoint[0], 0), depth_image.shape[1] - 1)
                ]
                depth_in_meters = depth_value * depth_scale

                if object_id not in tracked_objects:
                    tracked_objects[object_id] = {
                        'midpoints': deque(maxlen=window_size),
                        'depths': deque(maxlen=window_size)
                    }

                tracked_objects[object_id]['midpoints'].append(midpoint)
                tracked_objects[object_id]['depths'].append(depth_in_meters)

                avg_midpoint = np.mean(tracked_objects[object_id]['midpoints'], axis=0)
                avg_depth = np.mean(tracked_objects[object_id]['depths'])

                if len(tracked_objects[object_id]['midpoints']) > 1:
                    prev_midpoint = tracked_objects[object_id]['midpoints'][-2]
                    movement = np.linalg.norm(np.array(midpoint) - np.array(prev_midpoint))

                    # Track only if movement > movement_threshold
                    is_moving = movement > movement_threshold

                    if is_moving:
                        print(f"Object {object_id} moved to: {avg_midpoint}, Depth: {avg_depth:.3f}m")

                        x, y, z = convert_depth_pixel_to_metric_coordinate(
                            avg_depth, avg_midpoint[0], avg_midpoint[1], depth_intrinsics
                        )
                        transformed_midpoint = apply_transform(
                            np.array([[x, y, z]]), rotation_matrix, translation_values
                        )[0]
                        projected_point = project_to_2d(transformed_midpoint, depth_intrinsics)

                        moving_objects.append({
                            'id': object_id,
                            'midpoint': (avg_midpoint[0], avg_midpoint[1], avg_depth),
                            'bbox': (x1, y1, x2, y2),
                            'projected_point': projected_point,
                            'is_moving': is_moving  # Add movement status
                        })

                cv2.rectangle(color_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(color_image, (int(avg_midpoint[0]), int(avg_midpoint[1])), 4, (0, 0, 255), -1)

    previous_frame = gray

    return color_image, moving_objects

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

def render_point_cloud_with_midpoints(depth_frame, rotation_matrix, translation_values,
                                      x_threshold, y_threshold, z_threshold, moving_objects, intrinsics):
    pc = rs.pointcloud()
    points = pc.calculate(depth_frame)
    verts = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)

    verts[:, 0] = -verts[:, 0]  # Mirror horizontally
    verts_transformed = apply_transform(verts, rotation_matrix, translation_values)

    valid_mask = (
            (np.abs(verts_transformed[:, 0]) < x_threshold) &
            (np.abs(verts_transformed[:, 1]) < y_threshold) &
            (verts_transformed[:, 2] < z_threshold)
    )
    verts_transformed = verts_transformed[valid_mask]

    x, y, z = verts_transformed[:, 0], verts_transformed[:, 1], verts_transformed[:, 2]
    u = (x / z) * intrinsics.fx + intrinsics.ppx
    v = (y / z) * intrinsics.fy + intrinsics.ppy
    proj = np.vstack((u, v)).transpose().astype(np.int32)

    h, w = intrinsics.height, intrinsics.width
    mask = (proj[:, 0] >= 0) & (proj[:, 0] < w) & (proj[:, 1] >= 0) & (proj[:, 1] < h)
    proj, depths = proj[mask], z[mask]

    out = np.zeros((h, w), dtype=np.uint8)
    if len(depths) > 0:
        intensity = 255 * (1 - (depths - depths.min()) / (depths.max() - depths.min()))
        out[proj[:, 1], proj[:, 0]] = intensity.astype(np.uint8)

    out_color = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)

    # Filter only moving objects
    moving_objects = [obj for obj in moving_objects if obj['is_moving']]

    if moving_objects:
        # Identify the closest moving object by depth
        closest_object = min(moving_objects, key=lambda obj: obj['midpoint'][2])

        # Draw all objects, highlight the closest in purple
        for obj in moving_objects:
            if obj['projected_point']:
                x_p, y_p = obj['projected_point']
                if 0 <= x_p < w and 0 <= y_p < h:
                    if obj == closest_object:
                        x, y, depth = obj['midpoint']
                        get_image(x, y, depth, w, h)  # Call with correct values
                        color = (0, 0, 255)  # red for the closest object
                    else:
                        color = (0, 255, 255)  # Yellow for other objects

                    cv2.circle(out_color, (x_p, y_p), 4, color, -1)

    return out_color



if __name__ == "__main__":
    try:
        while True:
            frames = pipeline.poll_for_frames()
            if not frames:
                continue
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            if not color_frame or not depth_frame:
                continue
            color_image = np.asanyarray(color_frame.get_data())

            # Flip the RGB image horizontally
            color_image = cv2.flip(color_image, 1)  # 1 = Horizontal Flip

            depth_image = np.asanyarray(depth_frame.get_data())

            # Retrieve rotation, translation, and threshold values from GUI
            rotation_angles = [math.radians(control_panel.rotation_sliders[i].value()) for i in range(3)]
            translation_values = [control_panel.translation_sliders[i].value() / 100.0 for i in range(3)]
            x_threshold = control_panel.threshold_sliders[0].value() / 100.0
            y_threshold = control_panel.threshold_sliders[1].value() / 100.0
            z_threshold = control_panel.threshold_sliders[2].value() / 100.0

            rotation_matrix = get_rotation_matrix(rotation_angles)

            # Process YOLO tracking and render the point cloud with midpoints
            yolo_output, moving_objects = process_frame(
                color_image.copy(), depth_image, tracked_objects, rotation_matrix, translation_values, depth_intrinsics
            )
            point_cloud_output = render_point_cloud_with_midpoints(
                depth_frame, rotation_matrix, translation_values, x_threshold, y_threshold, z_threshold,
                moving_objects, depth_intrinsics
            )

            # Combine both outputs side-by-side
            combined_frame = np.hstack((yolo_output, point_cloud_output))

            # Display the combined frame
            cv2.imshow("YOLO + Point Cloud", combined_frame)

            # Process PyQt5 events and handle exit key
            app.processEvents()
            if cv2.waitKey(1) in (27, ord('q')):
                break
    finally:
        # Cleanup resources
        pipeline.stop()
        cv2.destroyAllWindows()