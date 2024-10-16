import math
import time
import cv2
import numpy as np
import pyrealsense2 as rs
import mediapipe as mp  # Import MediaPipe
import sys
from PyQt5 import QtWidgets, QtCore
from gui import TransformGUI  # Import the TransformGUI class
from render2d import render_2d
import socket
import math
import time
import cv2


# Initialize MediaPipe Pose
mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(min_detection_confidence=0.5)


class AppState:
    def __init__(self, *args, **kwargs):
        self.WIN_NAME = 'RealSense'
        self.pitch, self.yaw = 0, 0  # Set pitch and yaw to 0 to align straight on
        self.translation = np.array([0, 0, -1], dtype=np.float32)  # Centered on X and at a distance on Z
        self.distance = 2
        self.prev_mouse = 0, 0
        self.mouse_btns = [False, False, False]
        self.paused = False
        self.decimate = 0  # Set decimation to 0 to disable it temporarily
        self.scale = True
        self.color = True

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

# Configure the streams to have the same resolution
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Initialize alignment
align_to = rs.stream.color
align = rs.align(align_to)

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

# Initialize output image
out = np.empty((h, w, 3), dtype=np.uint8)




cv2.namedWindow(state.WIN_NAME, cv2.WINDOW_AUTOSIZE)
cv2.resizeWindow(state.WIN_NAME, w, h)
# cv2.setMouseCallback(state.WIN_NAME, mouse_cb)


def project(v):
    h, w = out.shape[:2]
    view_aspect = float(h) / w

    with np.errstate(divide='ignore', invalid='ignore'):
        proj = v[:, :-1] / v[:, -1, np.newaxis] * \
               (w * view_aspect, h) + (w / 2.0, h / 2.0)

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
    for i in range(0, n + 1):
        x = -s2 + i * s
        line3d(out, view(pos + np.dot((x, 0, -s2), rotation)),
               view(pos + np.dot((x, 0, s2), rotation)), color)
    for i in range(0, n + 1):
        z = -s2 + i * s
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
        v = view(verts)
        s = v[:, 2].argsort()[::-1]
        proj = project(v[s])
    else:
        proj = project(view(verts))

    if state.scale:
        proj *= 0.5 ** state.decimate

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
    np.clip(u, 0, ch - 1, out=u)
    np.clip(v, 0, cw - 1, out=v)

    # perform uv-mapping
    out[i[m], j[m]] = color[u[m], v[m]]


def run_gui():
    app = QtWidgets.QApplication(sys.argv)
    transform_gui = TransformGUI()
    transform_gui.show()

    try:
        while True:
            app.processEvents()
            if not state.paused:
                verts, texcoords, color_source, depth_intrinsics, keypoints_3d, landmark_to_point = process_frames_and_pointcloud(transform_gui)

            # Assuming the render_2d returns the closest moving blob coordinates (x, y, z)
            blob_coords = render_2d(out, verts, transform_gui)
            # if blob_coords:
            #     send_blob_coords(conn, blob_coords)  # Send the coordinates to the display system

            render_frame(verts, texcoords, color_source, depth_intrinsics, transform_gui, keypoints_3d, landmark_to_point)

            key = handle_key_inputs()
            if key in (27, ord("q")) or cv2.getWindowProperty(state.WIN_NAME, cv2.WND_PROP_AUTOSIZE) < 0:
                break
    finally:
        pipeline.stop()
        face_detection.close()
        # conn.close()

def process_frames_and_pointcloud(transform_gui):
    """Grab frames, apply decimation, filter, and transform point cloud."""
    frames = pipeline.wait_for_frames()

    # Align the depth frame to the color frame (for pose detection)
    aligned_frames = align.process(frames)

    # Get aligned depth and color frames (for pose estimation)
    aligned_depth_frame = aligned_frames.get_depth_frame()
    color_frame = aligned_frames.get_color_frame()

    # Use the original (unaligned) depth frame for the point cloud
    depth_frame = frames.get_depth_frame()

    # Optionally apply decimation filter (disabled for now)
    # depth_frame = decimate.process(depth_frame)
    depth_intrinsics = rs.video_stream_profile(depth_frame.profile).get_intrinsics()
    w, h = depth_intrinsics.width, depth_intrinsics.height

    depth_image = np.asanyarray(aligned_depth_frame.get_data())
    color_image = np.asanyarray(color_frame.get_data())

    # Convert color image to RGB for MediaPipe
    color_image_rgb = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)

    # Process the image and find pose landmarks
    results = face_detection.process(color_image_rgb)

# Extract face keypoints instead of pose landmarks
    keypoints_3d = []
    keypoint_indices = []
    if results.detections:
        for detection in results.detections:
            keypoints = detection.location_data.relative_keypoints
            # Only get the nose keypoint, which is the third one (index 2)
            nose_keypoint = keypoints[2]
            x_px = int(nose_keypoint.x * color_image.shape[1])
            y_px = int(nose_keypoint.y * color_image.shape[0])

            # Get depth value and deproject to 3D
            if 0 <= x_px < depth_image.shape[1] and 0 <= y_px < depth_image.shape[0]:
                depth = aligned_depth_frame.get_distance(x_px, y_px)
                if depth > 0:
                    point_3d = rs.rs2_deproject_pixel_to_point(depth_intrinsics, [x_px, y_px], depth)
                    point_3d[0] = -point_3d[0]  # Mirror the X-coordinate
                    keypoints_3d.append(point_3d)

    # Build a mapping from landmark index to 3D point
    landmark_to_point = {idx: point for idx, point in zip(keypoint_indices, keypoints_3d)}

    # Determine the source for the point cloud based on color or depth
    if state.color:
        mapped_frame, color_source = color_frame, color_image  # Use the mirrored image
    else:
        mapped_frame, color_source = depth_frame, color_image  # Use color image for texture

    # Process the point cloud and map it to the color or depth frame
    points = pc.calculate(depth_frame)  # Use the original depth frame for the point cloud
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

    return transformed_verts, texcoords, color_source, depth_intrinsics, keypoints_3d, landmark_to_point

def render_frame(verts, texcoords, color_source, depth_intrinsics, transform_gui, keypoints_3d, landmark_to_point):
    """Render the transformed point cloud in 3D, its 2D projection, and the RGB camera side by side, with face landmarks drawn."""
    now = time.time()

    # Create an output canvas large enough to display 3D and 2D views side by side
    out_3d = np.zeros((480, 640, 3), dtype=np.uint8)  # For 3D rendering
    out_2d = np.zeros((480, 640, 3), dtype=np.uint8)  # For 2D projection

    # Render the 3D point cloud and keypoints
    render_3d(out_3d, verts, texcoords, color_source, depth_intrinsics, transform_gui, keypoints_3d, landmark_to_point)

    # Project the 3D nose keypoint to 2D
    nose_keypoint_2d = None
    if keypoints_3d:  # Check if we have keypoints
        keypoints_3d_array = np.array(keypoints_3d)
        keypoints_3d_array = apply_gui_transform(keypoints_3d_array, transform_gui)

        keypoints_2d = project(view(keypoints_3d_array))

        if len(keypoints_2d) > 0:
            nose_keypoint_2d = keypoints_2d[0]  # Get the 2D position of the nose (first keypoint)

    # Render the 2D front view of the point cloud and pass the nose keypoint
    render_2d(out_2d, verts, transform_gui, nose_keypoint=nose_keypoint_2d)


    # Now draw the nose keypoint on the 2D render (same way as 3D)
    if keypoints_3d:
        keypoints_3d_array = np.array(keypoints_3d)
        keypoints_3d_array = apply_gui_transform(keypoints_3d_array, transform_gui)

        keypoints_2d = project(view(keypoints_3d_array))

        # Draw the nose keypoint in the 2D render
        if len(keypoints_2d) > 0:
            p = keypoints_2d[0]  # Nose is the first keypoint we processed
            if not np.isnan(p).any():
                x, y = int(p[0]), int(p[1])
                if 0 <= x < out_2d.shape[1] and 0 <= y < out_2d.shape[0]:
                    cv2.circle(out_2d, (x, y), 5, (0, 255, 255), -1)  # Yellow circle for the nose in 2D

    # Show the combined view
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


def render_3d(out, verts, texcoords, color_source, depth_intrinsics, transform_gui, keypoints_3d, landmark_to_point):
    """Render the 3D view of the point cloud and draw keypoints."""
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

    # Draw keypoints and connections in the 3D point cloud view
    if keypoints_3d:
        keypoints_3d_array = np.array(keypoints_3d)
        keypoints_3d_array = apply_gui_transform(keypoints_3d_array, transform_gui)

        keypoints_2d = project(view(keypoints_3d_array))

        # Draw keypoints as circles
        for p in keypoints_2d:
            if np.isnan(p).any():
                continue
            x, y = int(p[0]), int(p[1])
            if 0 <= x < out.shape[1] and 0 <= y < out.shape[0]:
                cv2.circle(out, (x, y), 5, (0, 255, 255), -1)


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



def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 65432))
    server_socket.listen(1)
    server_socket.setblocking(False)  # Set non-blocking mode
    print("Server is running and waiting for connections...")

    conn = None
    while conn is None:
        try:
            conn, addr = server_socket.accept()  # Accept a new connection
            print(f"Connected to {addr}")
        except BlockingIOError:
            # Non-blocking mode: just continue if no connection is ready
            pass

    return conn, server_socket

def send_blob_coords(conn, coords):
    try:
        message = f"{coords[0]},{coords[1]},{coords[2]}\n"
        conn.sendall(message.encode())
    except Exception as e:
        print(f"Error sending coordinates: {e}")

if __name__ == "__main__":
    # conn, server_socket = start_server()  # Start the server and wait for a connection
    # After the connection is established, you can run the GUI or other processes
    run_gui()  # Run the GUI and send blob coordinates using send_blob_coords