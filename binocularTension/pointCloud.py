# License: Apache 2.0. See LICENSE file in root directory.
# Copyright(c) 2015-2017 Intel Corporation. All Rights Reserved.

"""
OpenCV and Numpy Point cloud Software Renderer

This sample is mostly for demonstration and educational purposes.
It really doesn't offer the quality or performance that can be
achieved with hardware acceleration.

Usage:
------
Mouse:
    Drag with left button to rotate around pivot (thick small axes),
    with right button to translate and the wheel to zoom.

Keyboard:
    [p]     Pause
    [r]     Reset View
    [q\ESC] Quit
"""
from gui import TransformGUI  # Import the TransformGUI class

import math
import time
import cv2
import numpy as np
import pyrealsense2 as rs
import sys
from PyQt5 import QtWidgets, QtCore

class AppState:
    def __init__(self, *args, **kwargs):
        self.WIN_NAME = 'RealSense'
        self.pitch, self.yaw = 0, 0  # Set pitch and yaw to 0 to align straight on
        self.translation = np.array([0, 0, -1], dtype=np.float32)  # Centered on X and at a distance on Z
        self.distance = 2
        self.prev_mouse = 0, 0
        self.mouse_btns = [False, False, False]
        self.paused = False
        self.decimate = 1
        self.scale = True
        self.color = False

    def reset(self):
        # Reset pitch, yaw, and distance to default (straight on)
        self.pitch, self.yaw, self.distance = 0, 0, 2  # Keep the frame aligned with Y and centered on X
        self.translation[:] = 0, 0, -1  # Ensure the camera is centered and not rotated

    @property
    def rotation(self):
        # Apply no rotation for initial straight-on view
        Rx, _ = cv2.Rodrigues((self.pitch, 0, 0))
        Ry, _ = cv2.Rodrigues((0, self.yaw, 0))
        return np.dot(Ry, Rx).astype(np.float32)

    @property
    def pivot(self):
        # The pivot point is the position at which the camera will rotate around
        return self.translation + np.array((0, 0, self.distance), dtype=np.float32)

state = AppState()
def apply_gui_transform(verts, gui):
    # Get translation and rotation values from the GUI
    tx, ty, tz = gui.get_translation()
    rx, ry, rz = gui.get_rotation()

    # Apply translation
    verts[:, 0] += tx / 100.0
    verts[:, 1] += ty / 100.0
    verts[:, 2] += tz / 100.0

    # Apply rotation (convert to radians first)
    rx, ry, rz = math.radians(rx), math.radians(ry), math.radians(rz)

    # Rotation matrices around x, y, and z axes
    Rx = np.array([[1, 0, 0],
                   [0, math.cos(rx), -math.sin(rx)],
                   [0, math.sin(rx), math.cos(rx)]])

    Ry = np.array([[math.cos(ry), 0, math.sin(ry)],
                   [0, 1, 0],
                   [-math.sin(ry), 0, math.cos(ry)]])

    Rz = np.array([[math.cos(rz), -math.sin(rz), 0],
                   [math.sin(rz), math.cos(rz), 0],
                   [0, 0, 1]])

    # Apply rotations
    verts = np.dot(verts, Rx)
    verts = np.dot(verts, Ry)
    verts = np.dot(verts, Rz)

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
decimate.set_option(rs.option.filter_magnitude, 2 ** state.decimate)
colorizer = rs.colorizer()


def mouse_cb(event, x, y, flags, param):

    if event == cv2.EVENT_LBUTTONDOWN:
        state.mouse_btns[0] = True

    if event == cv2.EVENT_LBUTTONUP:
        state.mouse_btns[0] = False

    if event == cv2.EVENT_RBUTTONDOWN:
        state.mouse_btns[1] = True

    if event == cv2.EVENT_RBUTTONUP:
        state.mouse_btns[1] = False

    if event == cv2.EVENT_MBUTTONDOWN:
        state.mouse_btns[2] = True

    if event == cv2.EVENT_MBUTTONUP:
        state.mouse_btns[2] = False

    if event == cv2.EVENT_MOUSEMOVE:

        h, w = out.shape[:2]
        dx, dy = x - state.prev_mouse[0], y - state.prev_mouse[1]

        if state.mouse_btns[0]:
            state.yaw += float(dx) / w * 2
            state.pitch -= float(dy) / h * 2

        elif state.mouse_btns[1]:
            dp = np.array((dx / w, dy / h, 0), dtype=np.float32)
            state.translation -= np.dot(state.rotation, dp)

        elif state.mouse_btns[2]:
            dz = math.sqrt(dx**2 + dy**2) * math.copysign(0.01, -dy)
            state.translation[2] += dz
            state.distance -= dz

    if event == cv2.EVENT_MOUSEWHEEL:
        dz = math.copysign(0.1, flags)
        state.translation[2] += dz
        state.distance -= dz

    state.prev_mouse = (x, y)


cv2.namedWindow(state.WIN_NAME, cv2.WINDOW_AUTOSIZE)
cv2.resizeWindow(state.WIN_NAME, w, h)
cv2.setMouseCallback(state.WIN_NAME, mouse_cb)


def project(v):
    """project 3d vector array to 2d"""
    h, w = out.shape[:2]
    view_aspect = float(h)/w

    # ignore divide by zero for invalid depth
    with np.errstate(divide='ignore', invalid='ignore'):
        proj = v[:, :-1] / v[:, -1, np.newaxis] * \
               (w*view_aspect, h) + (w/2.0, h/2.0)

    # near clipping
    znear = 0.03
    proj[v[:, 2] < znear] = np.nan
    return proj


def view(v):
    """apply view transformation on vector array"""
    return np.dot(v - state.pivot, state.rotation) + state.pivot - state.translation


def line3d(out, pt1, pt2, color=(0x80, 0x80, 0x80), thickness=1):
    """draw a 3d line from pt1 to pt2"""
    p0 = project(pt1.reshape(-1, 3))[0]
    p1 = project(pt2.reshape(-1, 3))[0]
    if np.isnan(p0).any() or np.isnan(p1).any():
        return
    p0 = tuple(p0.astype(int))
    p1 = tuple(p1.astype(int))
    rect = (0, 0, out.shape[1], out.shape[0])
    inside, p0, p1 = cv2.clipLine(rect, p0, p1)
    if inside:
        cv2.line(out, p0, p1, color, thickness, cv2.LINE_AA)


def grid(out, pos, rotation=np.eye(3), size=1, n=10, color=(0x80, 0x80, 0x80)):
    """draw a grid on xz plane"""
    pos = np.array(pos)
    s = size / float(n)
    s2 = 0.5 * size
    for i in range(0, n+1):
        x = -s2 + i*s
        line3d(out, view(pos + np.dot((x, 0, -s2), rotation)),
               view(pos + np.dot((x, 0, s2), rotation)), color)
    for i in range(0, n+1):
        z = -s2 + i*s
        line3d(out, view(pos + np.dot((-s2, 0, z), rotation)),
               view(pos + np.dot((s2, 0, z), rotation)), color)


def axes(out, pos, rotation=np.eye(3), size=0.075, thickness=2):
    """draw 3d axes"""
    line3d(out, pos, pos +
           np.dot((0, 0, size), rotation), (0xff, 0, 0), thickness)
    line3d(out, pos, pos +
           np.dot((0, size, 0), rotation), (0, 0xff, 0), thickness)
    line3d(out, pos, pos +
           np.dot((size, 0, 0), rotation), (0, 0, 0xff), thickness)


def frustum(out, intrinsics, color=(0x40, 0x40, 0x40)):
    """draw camera's frustum"""
    orig = view([0, 0, 0])
    w, h = intrinsics.width, intrinsics.height

    for d in range(1, 6, 2):
        def get_point(x, y):
            p = rs.rs2_deproject_pixel_to_point(intrinsics, [x, y], d)
            line3d(out, orig, view(p), color)
            return p

        top_left = get_point(0, 0)
        top_right = get_point(w, 0)
        bottom_right = get_point(w, h)
        bottom_left = get_point(0, h)

        line3d(out, view(top_left), view(top_right), color)
        line3d(out, view(top_right), view(bottom_right), color)
        line3d(out, view(bottom_right), view(bottom_left), color)
        line3d(out, view(bottom_left), view(top_left), color)


def pointcloud(out, verts, texcoords, color, painter=True):
    """draw point cloud with optional painter's algorithm"""
    if painter:
        # Painter's algo, sort points from back to front

        # get reverse sorted indices by z (in view-space)
        # https://gist.github.com/stevenvo/e3dad127598842459b68
        v = view(verts)
        s = v[:, 2].argsort()[::-1]
        proj = project(v[s])
    else:
        proj = project(view(verts))

    if state.scale:
        proj *= 0.5**state.decimate

    h, w = out.shape[:2]

    # proj now contains 2d image coordinates
    j, i = proj.astype(np.uint32).T

    # create a mask to ignore out-of-bound indices
    im = (i >= 0) & (i < h)
    jm = (j >= 0) & (j < w)
    m = im & jm

    cw, ch = color.shape[:2][::-1]
    if painter:
        # sort texcoord with same indices as above
        # texcoords are [0..1] and relative to top-left pixel corner,
        # multiply by size and add 0.5 to center
        v, u = (texcoords[s] * (cw, ch) + 0.5).astype(np.uint32).T
    else:
        v, u = (texcoords * (cw, ch) + 0.5).astype(np.uint32).T
    # clip texcoords to image
    np.clip(u, 0, ch-1, out=u)
    np.clip(v, 0, cw-1, out=v)

    # perform uv-mapping
    out[i[m], j[m]] = color[u[m], v[m]]


out = np.empty((h, w, 3), dtype=np.uint8)

def run_gui():
    app = QtWidgets.QApplication(sys.argv)
    transform_gui = TransformGUI()
    transform_gui.show()

    while True:
        app.processEvents()  # Update the PyQt5 GUI

        if not state.paused:
            verts, texcoords, color_source, depth_intrinsics = process_frames_and_pointcloud(transform_gui)

        render_frame(verts, texcoords, color_source, depth_intrinsics, transform_gui)

        key = handle_key_inputs()
        if key in (27, ord("q")) or cv2.getWindowProperty(state.WIN_NAME, cv2.WND_PROP_AUTOSIZE) < 0:
            break

    pipeline.stop()  # Stop streaming

def process_frames_and_pointcloud(transform_gui):
    """Grab frames, apply decimation, filter, and transform point cloud."""
    frames = pipeline.wait_for_frames()
    depth_frame = frames.get_depth_frame()
    color_frame = frames.get_color_frame()

    depth_frame = decimate.process(depth_frame)
    depth_intrinsics = rs.video_stream_profile(depth_frame.profile).get_intrinsics()
    w, h = depth_intrinsics.width, depth_intrinsics.height

    depth_image = np.asanyarray(depth_frame.get_data())
    color_image = np.asanyarray(color_frame.get_data())

    # Mirror the color image horizontally
    color_image = cv2.flip(color_image, 1)  # 1 means flipping around the y-axis

    depth_colormap = np.asanyarray(colorizer.colorize(depth_frame).get_data())

    # Determine the source for the point cloud based on color or depth
    if state.color:
        mapped_frame, color_source = color_frame, color_image  # Use the mirrored image
    else:
        mapped_frame, color_source = depth_frame, depth_colormap

    # Process the point cloud and map it to the color or depth frame
    points = pc.calculate(depth_frame)
    pc.map_to(mapped_frame)
    verts = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)  # xyz
    texcoords = np.asanyarray(points.get_texture_coordinates()).view(np.float32).reshape(-1, 2)  # uv

    # Get the x, y, and z (depth) thresholds from the GUI
    x_threshold, y_threshold, z_threshold = transform_gui.get_thresholds()

    # Filter out points that exceed the thresholds
    valid_indices = (np.abs(verts[:, 0]) <= x_threshold) & \
                    (np.abs(verts[:, 1]) <= y_threshold) & \
                    (verts[:, 2] <= z_threshold)

    verts = verts[valid_indices]
    texcoords = texcoords[valid_indices]

    # Apply transformation based on GUI values
    transformed_verts = apply_gui_transform(verts, transform_gui)
    transformed_verts[:, 0] = -transformed_verts[:, 0]  # Negate x-coordinates

    return transformed_verts, texcoords, color_source, depth_intrinsics

def render_frame(verts, texcoords, color_source, depth_intrinsics, transform_gui):
    """Render the transformed point cloud in 3D and its 2D projection side by side."""
    now = time.time()

    # Create an output canvas large enough to display both 2D and 3D views side by side
    out_3d = np.zeros((480, 640, 3), dtype=np.uint8)  # For 3D rendering
    out_2d = np.zeros((480, 640, 3), dtype=np.uint8)  # For 2D projection

    # Render the 3D point cloud
    render_3d(out_3d, verts, texcoords, color_source, depth_intrinsics, transform_gui)

    # Render the 2D front view of the point cloud
    render_2d(out_2d, verts, transform_gui)

    # Combine the two views side by side
    combined_view = np.hstack((out_3d, out_2d))

    # Calculate frame timing
    dt = time.time() - now
    if dt > 0:
        fps = 1.0 / dt
    else:
        fps = 0  # Handle the case where dt is zero

    cv2.setWindowTitle(
        state.WIN_NAME,
        f"3D and 2D Views {combined_view.shape[1]}x{combined_view.shape[0]} @ {fps}FPS ({dt * 1000:.2f}ms)"
    )

    # Show the combined view
    cv2.imshow(state.WIN_NAME, combined_view)

def render_3d(out, verts, texcoords, color_source, depth_intrinsics, transform_gui):
    """Render the 3D view of the point cloud."""
    # Existing 3D rendering logic
    out.fill(0)

    # Get Y-axis translation from the GUI
    _, y_translation, _ = transform_gui.get_translation()

    # Render grid with adjusted Y-axis position
    grid(out, (0, 0.5 + y_translation / 100.0, 1), size=1, n=10)

    # Render the camera frustum
    frustum(out, depth_intrinsics)

    # Render axes
    axes(out, view([0, 0, 0]), state.rotation, size=0.1, thickness=1)
    # Render point cloud
    h, w = depth_intrinsics.height, depth_intrinsics.width
    if not state.scale or out.shape[:2] == (h, w):
        pointcloud(out, verts, texcoords, color_source)
    else:
        tmp = np.zeros((h, w, 3), dtype=np.uint8)
        pointcloud(tmp, verts, texcoords, color_source)
        tmp = cv2.resize(tmp, out.shape[:2][::-1], interpolation=cv2.INTER_NEAREST)
        np.putmask(out, tmp > 0, tmp)

def render_2d(out, verts, transform_gui, fixed_scale=300.0):
    """Render the 2D representation of the 3D point cloud (front view) with smoothing."""
    out.fill(0)

    # Project to 2D and scale
    verts_2d = verts[:, :2]  # Keep only x and y coordinates
    scale = fixed_scale
    verts_2d[:, 0] = verts_2d[:, 0] * scale
    verts_2d[:, 1] = verts_2d[:, 1] * scale

    center_x = out.shape[1] // 2
    center_y = out.shape[0] // 2
    verts_2d[:, 0] += center_x
    verts_2d[:, 1] += center_y

    # Create a mask for valid points
    valid_points = (verts_2d[:, 0] >= 0) & (verts_2d[:, 0] < out.shape[1]) & \
                   (verts_2d[:, 1] >= 0) & (verts_2d[:, 1] < out.shape[0])

    # Get valid coordinates
    valid_x = verts_2d[valid_points][:, 0].astype(int)
    valid_y = verts_2d[valid_points][:, 1].astype(int)

    # Create a heatmap
    heatmap = np.zeros(out.shape[:2], dtype=np.float32)
    for x, y in zip(valid_x, valid_y):
        cv2.circle(heatmap, (x, y), 3, 1, -1)

    # Apply Gaussian blur to the heatmap
    heatmap = cv2.GaussianBlur(heatmap, (11, 11), 0)

    # Normalize the heatmap
    heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX)
    heatmap = heatmap.astype(np.uint8)

    # Threshold the heatmap to create a binary mask
    _, binary_mask = cv2.threshold(heatmap, 50, 255, cv2.THRESH_BINARY)

    # Apply morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)

    # Find contours
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours by area
    min_area_threshold = 100
    large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area_threshold]

    # Draw filled contours
    cv2.drawContours(out, large_contours, -1, (255, 255, 255), -1)

    # Apply edge smoothing
    out = cv2.GaussianBlur(out, (5, 5), 0)

    return out
def draw_marker(out, position, color=(255, 255, 255), size=5, label=None):
    """Draw a small marker (point) at a specific 3D position, with optional label."""
    screen_pos = project_to_screen(position, out.shape)
    cv2.circle(out, screen_pos, size, color, -1)

    if label:
        cv2.putText(out, label, (screen_pos[0] + 10, screen_pos[1] + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

def project_to_screen(position, screen_shape):
    """Convert a 3D point to 2D screen coordinates."""
    x, y, z = position
    # Basic projection logic (placeholder, should be replaced with actual 3D-to-2D projection)
    screen_x = int((x + 1) * screen_shape[1] // 2)  # Normalize x to screen width
    screen_y = int((1 - y) * screen_shape[0] // 2)  # Normalize y to screen height (invert for screen coordinates)

    return (screen_x, screen_y)

def handle_key_inputs():
    """Handle keyboard inputs for controlling the GUI."""
    key = cv2.waitKey(1)
    if key == ord("r"):
        state.reset()
    elif key == ord("p"):
        state.paused ^= True
    elif key == ord("d"):
        state.decimate = (state.decimate + 1) % 3
        decimate.set_option(rs.option.filter_magnitude, 2 ** state.decimate)
    return key



if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    # Your GUI initialization code here
    run_gui()