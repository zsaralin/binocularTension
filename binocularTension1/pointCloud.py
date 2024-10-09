import cv2
import numpy as np
import pyrealsense2 as rs
import math
from gui import ControlPanel
from PyQt5.QtWidgets import QApplication
import sys
from ultralytics import YOLO
from collections import deque
from multiperson import get_processed_frame

# Helper function: get_rotation_matrix
def get_rotation_matrix(angles):
    """Calculates a 3D rotation matrix from rotation angles."""
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

# Helper function: apply_transform
def apply_transform(verts, rotation_matrix, translation_values):
    """Applies a rotation matrix and translation vector to vertices."""
    verts = np.dot(verts, rotation_matrix.T)
    verts += np.array(translation_values)
    return verts

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()

pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()

# Get the depth scale
depth_sensor = device.first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()

found_rgb = False
for s in device.sensors:
    if s.get_info(rs.camera_info.name) == 'RGB Camera':
        found_rgb = True
        break
if not found_rgb:
    print("The demo requires Depth camera with Color sensor")
    exit(0)

config.enable_stream(rs.stream.depth, rs.format.z16, 30)
config.enable_stream(rs.stream.color, rs.format.bgr8, 30)

# Start streaming
profile = pipeline.start(config)

# Get stream profile and camera intrinsics
depth_intrinsics = rs.video_stream_profile(profile.get_stream(rs.stream.depth)).get_intrinsics()
w, h = depth_intrinsics.width, depth_intrinsics.height

# Processing blocks
pc = rs.pointcloud()
decimate = rs.decimation_filter()
decimate.set_option(rs.option.filter_magnitude, 2)
colorizer = rs.colorizer()

out = np.empty((h, w, 3), dtype=np.uint8)

# Initialize the PyQt5 GUI
app = QApplication(sys.argv)
control_panel = ControlPanel()  # Create the control panel instance
control_panel.show()

# Load the YOLOv8 model
model = YOLO("yolov8n.pt")
model.verbose = False

# Dictionary to store object tracking data
tracked_objects = {}

# Moving average window size
window_size = 5

# Movement threshold (in pixels)
movement_threshold = 10

def project_point(point_3d, rotation_matrix, translation_values, intrinsics):
    # Apply rotation and translation
    point_3d = np.dot(rotation_matrix, point_3d) + translation_values
    
    # Project 3D point to 2D
    x = point_3d[0] / point_3d[2] * intrinsics.fx + intrinsics.ppx
    y = point_3d[1] / point_3d[2] * intrinsics.fy + intrinsics.ppy
    
    return int(x), int(y)

while True:
    # Grab camera data
    frames = pipeline.wait_for_frames()

    depth_frame = frames.get_depth_frame()
    color_frame = frames.get_color_frame()

    depth_frame = decimate.process(depth_frame)

    depth_image = np.asanyarray(depth_frame.get_data())
    color_image = np.asanyarray(color_frame.get_data())

    points = pc.calculate(depth_frame)
    pc.map_to(color_frame)

    # Pointcloud data to arrays
    v, t = points.get_vertices(), points.get_texture_coordinates()
    verts = np.asanyarray(v).view(np.float32).reshape(-1, 3)  # xyz
    texcoords = np.asanyarray(t).view(np.float32).reshape(-1, 2)  # uv

    # Get updated rotation matrix based on the PyQt5 sliders
    rotation_angles = [
        math.radians(control_panel.rotation_sliders[0].value()),
        math.radians(control_panel.rotation_sliders[1].value()),
        math.radians(control_panel.rotation_sliders[2].value())
    ]
    rotation_matrix = get_rotation_matrix(rotation_angles)

    # Get translation values from the PyQt5 sliders
    translation_values = [
        control_panel.translation_sliders[0].value() / 100.0,
        control_panel.translation_sliders[1].value() / 100.0,
        control_panel.translation_sliders[2].value() / 100.0
    ]

    # Apply rotation and translation to the vertices
    verts = apply_transform(verts, rotation_matrix, translation_values)

    # Get threshold values from the PyQt5 sliders
    thresholds = {
        'x_threshold': control_panel.threshold_sliders[0].value() / 100.0,
        'y_threshold': control_panel.threshold_sliders[1].value() / 100.0,
        'z_threshold': control_panel.threshold_sliders[2].value() / 100.0,
    }

    # Apply thresholds to filter the vertices
    x_filter = np.abs(verts[:, 0]) < thresholds['x_threshold']
    y_filter = np.abs(verts[:, 1]) < thresholds['y_threshold']
    z_filter = verts[:, 2] < thresholds['z_threshold']
    threshold_mask = x_filter & y_filter & z_filter
    verts = verts[threshold_mask]
    texcoords = texcoords[threshold_mask]

    # Render point cloud
    out.fill(0)

    def project(v):
        h, w = out.shape[:2]
        view_aspect = float(h) / w

        with np.errstate(divide='ignore', invalid='ignore'):
            proj = v[:, :-1] / v[:, -1, np.newaxis] * \
                   (w * view_aspect, h) + (w / 2.0, h / 2.0)

        znear = 0.03
        proj[v[:, 2] < znear] = np.nan
        return proj

    proj = project(verts)
    j, i = proj.astype(np.uint32).T

    im = (i >= 0) & (i < h)
    jm = (j >= 0) & (j < w)
    m = im & jm

    cw, ch = color_image.shape[:2][::-1]
    v, u = (texcoords * (cw, ch) + 0.5).astype(np.uint32).T
    np.clip(u, 0, ch - 1, out=u)
    np.clip(v, 0, cw - 1, out=v)

    out[i[m], j[m]] = color_image[u[m], v[m]]

    # Get the processed frame with YOLO detections and moving objects
    yolo_frame, moving_objects = get_processed_frame(pipeline, model, tracked_objects, window_size, movement_threshold)

    # Create a blank canvas for the right side
    blank_canvas = np.zeros_like(out)

    if yolo_frame is not None:
        # Resize yolo_frame to match the height of the point cloud output
        yolo_frame_resized = cv2.resize(yolo_frame, (out.shape[1], out.shape[0]))
    else:
        yolo_frame_resized = blank_canvas.copy()

    # Draw bounding boxes on the point cloud
    for obj in moving_objects:
        bbox = obj['bbox']
        x1, y1, x2, y2 = map(int, bbox)

        # Project bounding box corners to 3D
        corners_3d = []
        for x, y in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]:
            depth = depth_image[y, x]
            if depth > 0:
                z = depth * depth_scale
                point_3d = np.array([(x - depth_intrinsics.ppx) * z / depth_intrinsics.fx,
                                     (y - depth_intrinsics.ppy) * z / depth_intrinsics.fy,
                                     z])
                corners_3d.append(point_3d)

        # Draw the bounding box on the point cloud
        if len(corners_3d) == 4:
            for i in range(4):
                start = project_point(corners_3d[i], rotation_matrix, translation_values, depth_intrinsics)
                end = project_point(corners_3d[(i + 1) % 4], rotation_matrix, translation_values, depth_intrinsics)
                cv2.line(out, start, end, (0, 255, 0), 2)

        # Draw the object ID
        if corners_3d:
            center_3d = np.mean(corners_3d, axis=0)
            center_pixel = project_point(center_3d, rotation_matrix, translation_values, depth_intrinsics)
            cv2.putText(out, f"ID: {obj['id']}", (center_pixel[0], center_pixel[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Combine the point cloud (left) and the YOLO frame or blank canvas (right) side-by-side
    combined_image = np.hstack((out, yolo_frame_resized))

    # Display the combined image in a static window
    cv2.imshow('Point Cloud and YOLO Detections', combined_image)

    # Process PyQt5 events
    app.processEvents()

    # Handle key press to exit
    key = cv2.waitKey(1)
    if key in (27, ord("q")):
        break

# Stop streaming
pipeline.stop()
cv2.destroyAllWindows()