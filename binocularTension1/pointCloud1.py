import cv2
import numpy as np
import pyrealsense2 as rs
import math
from gui import ControlPanel
from PyQt5.QtWidgets import QApplication
import sys

# Helper function: get_rotation_matrix
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

# Helper function: apply_transform
def apply_transform(verts, rotation_matrix, translation_values):
    verts = np.dot(verts, rotation_matrix.T)
    verts += np.array(translation_values)
    return verts

# Initialize Kalman filter for blob tracking
def initialize_kalman_filter():
    kf = cv2.KalmanFilter(4, 2)
    kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                     [0, 1, 0, 0]], np.float32)
    kf.transitionMatrix = np.array([[1, 0, 1, 0],
                                    [0, 1, 0, 1],
                                    [0, 0, 1, 0],
                                    [0, 0, 0, 1]], np.float32)
    kf.processNoiseCov = np.eye(4, dtype=np.float32) * 1e-3  # Increased noise removal
    kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 1e-2  # Increased noise removal
    kf.errorCovPost = np.eye(4, dtype=np.float32)
    return kf

# Apply Kalman filter to smooth the blob positions
def apply_kalman_filter(kf, position):
    kf.correct(position.reshape(2, 1))
    prediction = kf.predict()
    return prediction[:2].flatten()

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

out = np.empty((h, w, 3), dtype=np.uint8)

# Initialize the PyQt5 GUI
app = QApplication(sys.argv)
control_panel = ControlPanel()
control_panel.show()

# Define the downscale factor for the 2D side
downscale_factor = 0.5
dw, dh = int(w * downscale_factor), int(h * downscale_factor)

# Initialize Kalman filters for blob tracking
kalman_filters = []

# Define minimum blob size
min_blob_size = 100  # Adjust this value as needed

# Initialize previous positions for EMA smoothing
previous_positions = []

# Define smoothing factor for EMA
alpha = 0.5  # Adjust this value as needed

while True:
    # Grab camera data
    frames = pipeline.wait_for_frames()
    depth_frame = frames.get_depth_frame()
    color_frame = frames.get_color_frame()
    depth_frame = decimate.process(depth_frame)

    # Convert depth frame to grayscale with increased contrast
    depth_image = np.asanyarray(depth_frame.get_data())
    depth_image = cv2.convertScaleAbs(depth_image, alpha=0.1)  # Increase alpha to enhance contrast
    depth_gray_image = cv2.cvtColor(depth_image, cv2.COLOR_GRAY2BGR)  # Convert to BGR format

    # Invert the grayscale image so closer points are white and farther points are black
    depth_gray_image = cv2.bitwise_not(depth_gray_image)

    points = pc.calculate(depth_frame)
    pc.map_to(depth_frame)

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

    # Use inverted grayscale depth image for point cloud coloring
    cw, ch = depth_gray_image.shape[:2][::-1]
    v, u = (texcoords * (cw, ch) + 0.5).astype(np.uint32).T
    np.clip(u, 0, ch - 1, out=u)
    np.clip(v, 0, cw - 1, out=v)

    out[i[m], j[m]] = depth_gray_image[u[m], v[m]]

    # Create an empty canvas for the right side
    empty_canvas = np.zeros((dh, dw, 3), dtype=np.uint8)

    # Take a screenshot of the point cloud display
    screenshot = out.copy()

    # Resize the screenshot to fit the right canvas
    screenshot_resized = cv2.resize(screenshot, (dw, dh))

    # Convert the screenshot to grayscale for blob detection
    gray_screenshot = cv2.cvtColor(screenshot_resized, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to isolate blobs
    _, thresh = cv2.threshold(gray_screenshot, 1, 255, cv2.THRESH_BINARY)

    # Find contours (blobs) based on the thresholded image
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter out small blobs
    contours = [contour for contour in contours if cv2.contourArea(contour) >= min_blob_size]

    # Initialize Kalman filters for new blobs
    if len(kalman_filters) < len(contours):
        for _ in range(len(contours) - len(kalman_filters)):
            kalman_filters.append(initialize_kalman_filter())

    # Initialize previous positions for new blobs
    if len(previous_positions) < len(contours):
        for _ in range(len(contours) - len(previous_positions)):
            previous_positions.append(None)

    for idx, contour in enumerate(contours):
        # Calculate centroid of the blob
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            position = np.array([cX, cY], dtype=np.float32)

            # Apply Kalman filter to smooth the blob position
            smoothed_position = apply_kalman_filter(kalman_filters[idx], position)

            # Apply EMA smoothing
            if previous_positions[idx] is None:
                previous_positions[idx] = smoothed_position
            else:
                previous_positions[idx] = alpha * smoothed_position + (1 - alpha) * previous_positions[idx]

            # Draw the contours and smoothed centroid on the right canvas
            cv2.drawContours(empty_canvas, [contour], -1, (255, 255, 255), 2)  # White contours

    # Combine the point cloud (left) and the contours (right) side-by-side
    combined_image = np.hstack((out, cv2.resize(empty_canvas, (w, h))))

    # Display the combined image
    cv2.imshow('Point Cloud and Blobs', combined_image)

    # Process PyQt5 events
    app.processEvents()

    # Handle key press to exit
    key = cv2.waitKey(1)
    if key in (27, ord("q")):
        break

# Stop streaming
pipeline.stop()
cv2.destroyAllWindows()