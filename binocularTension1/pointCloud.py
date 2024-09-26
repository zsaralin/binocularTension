import cv2
import numpy as np
import pyrealsense2 as rs
import math
from gui import ControlPanel  # Import the new ControlPanel class
from render2d import render_2d
import time
from filterpy.kalman import KalmanFilter

# prev_time = time.time()
# fps = 0

# Initialize Kalman filter
def init_kalman_filter():
    kf = KalmanFilter(dim_x=4, dim_z=2)  # State: [x, y, dx, dy], Measurement: [x, y]

    kf.F = np.array([[1, 0, 1, 0],
                     [0, 1, 0, 1],
                     [0, 0, 1, 0],
                     [0, 0, 0, 1]])  # State transition matrix

    kf.H = np.array([[1, 0, 0, 0],
                     [0, 1, 0, 0]])  # Measurement function

    # Increase measurement noise to filter out noisy observations
    kf.R = np.array([[50, 0],
                     [0, 50]])  # You can experiment with higher values to reduce noise

    # Decrease process noise to make the filter smoother
    kf.Q = np.array([[0.1, 0, 0, 0],
                     [0, 0.1, 0, 0],
                     [0, 0, 0.1, 0],
                     [0, 0, 0, 0.1]])  # Lower values will smooth out movement more

    return kf

# Blob tracking function
# Blob tracking function with contour visualization and rescaling
def track_blobs(out, previous_blobs, kf, contour_canvas):
    # Convert the point cloud output 'out' to grayscale
    gray_out = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to isolate blobs (based on the grayscale point cloud)
    _, thresh = cv2.threshold(gray_out, 50, 255, cv2.THRESH_BINARY)

    # Find contours (blobs) based on the thresholded point cloud
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    current_blobs = []
    for contour in contours:
        # Draw the contours on the right canvas
        cv2.drawContours(contour_canvas, [contour], -1, (255, 255, 255), 2)  # White contours

        # Calculate centroid of the blob
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            # Update Kalman filter
            kf.predict()
            kf.update(np.array([cX, cY]))

            # Get the filtered position
            filtered_pos = kf.x[:2]

            current_blobs.append(filtered_pos)

    return current_blobs

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
pipeline.start(config)

# Get stream profile and camera intrinsics
profile = pipeline.get_active_profile()
depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
depth_intrinsics = depth_profile.get_intrinsics()
w, h = depth_intrinsics.width, depth_intrinsics.height

# Processing blocks
pc = rs.pointcloud()
decimate = rs.decimation_filter()
decimate.set_option(rs.option.filter_magnitude, 2)
colorizer = rs.colorizer()

out = np.empty((h, w, 3), dtype=np.uint8)

# Initialize the PyQt5 GUI
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
control_panel = ControlPanel()  # Create the control panel instance
control_panel.show()

# Initialize Kalman filter
kf = init_kalman_filter()

# Track previous blob positions
previous_blobs = []

while True:

    # Grab camera data
    frames = pipeline.wait_for_frames()

    depth_frame = frames.get_depth_frame()
    color_frame = frames.get_color_frame()

    depth_frame = decimate.process(depth_frame)

    depth_image = np.asanyarray(depth_frame.get_data())
    color_image = np.asanyarray(color_frame.get_data())

    depth_colormap = np.asanyarray(colorizer.colorize(depth_frame).get_data())

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
        'movement_threshold': control_panel.threshold_sliders[3].value()
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

    # Create a new blank canvas for drawing contours on the right
    contour_canvas = np.zeros_like(out)

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

    # Call render_2d to draw contours on the right canvas
    # render_2d(out, verts, contour_canvas, depth_image, project=project)

    # Track blobs
    canvas_width, canvas_height = out.shape[1], out.shape[0]
    depth_width, depth_height = depth_image.shape[1], depth_image.shape[0]

    # Call track_blobs and draw contours + centroids
    current_blobs = track_blobs(out, previous_blobs, kf, contour_canvas)

    # Update previous_blobs for the next iteration
    previous_blobs = current_blobs

    # Combine the point cloud (left) and the contours (right) side-by-side
    combined_image = np.hstack((out, contour_canvas))

    # Display the combined image
    current_time = time.time()

    # Calculate FPS
    # current_time = time.time()
    # fps = 1 / (current_time - prev_time)
    # prev_time = current_time

    # Display the combined image in a static window
    cv2.imshow('Point Cloud and Contours', combined_image)

    # Update window title with FPS
    cv2.setWindowTitle('Point Cloud and Contours', f'Point Cloud and Contours - FPS: {0:.2f}')

    # Process PyQt5 events
    app.processEvents()

    # Handle key press to exit
    key = cv2.waitKey(1)
    if key in (27, ord("q")):
        break

# Stop streaming
pipeline.stop()
cv2.destroyAllWindows()
