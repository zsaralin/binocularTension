import cv2
import numpy as np
import pyrealsense2 as rs
import math
from PyQt5.QtWidgets import QApplication
from ultralytics import YOLO
import sys
from gui import ControlPanel
from deep_sort_realtime.deepsort_tracker import DeepSort
from transform_utils import get_rotation_matrix, apply_transform, rotation_matrix
from drawing_utils import (
    draw_person_bounding_boxes,
    draw_movement_boxes,
    draw_keypoints_manually,
    draw_skeleton,
    KEYPOINT_CONNECTIONS,
    bbox_iou
)
from headpoint_utils import (
    smooth_head_point,
    compute_general_head_point,
    compute_movement_points
)
from movement_detection import (
    detect_movement,
    get_non_person_movement_boxes
)
from active_movement_logic import update_active_movement
from point_cloud_view import mouse_event, draw_frustum
from pyglet.gl import *
import ctypes

# AppState class to manage rotation and translation

# Create an offscreen buffer for Pyglet rendering
fbo = GLuint()
glGenFramebuffers(1, ctypes.byref(fbo))
glBindFramebuffer(GL_FRAMEBUFFER, fbo)

# Create a texture to render to
texture = GLuint()
glGenTextures(1, ctypes.byref(texture))
glBindTexture(GL_TEXTURE_2D, texture)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 640, 480, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0)

# Check if framebuffer is complete
if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
    print("Framebuffer not complete")
glBindFramebuffer(GL_FRAMEBUFFER, 0)
# Function to draw spheres at 3D coordinates
def draw_sphere(x, y, z, radius=0.05, slices=16, stacks=16):
    """Draws a sphere using pyglet OpenGL."""
    quad = gluNewQuadric()
    glPushMatrix()
    glTranslatef(x, y, z)
    gluSphere(quad, radius, slices, stacks)
    glPopMatrix()
class AppState:
    def __init__(self):
        self.pitch, self.yaw = 0, 0  # Rotation angles in degrees
        self.translation = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.distance = 0.0  # For zooming
        self.mouse_btns = [False, False, False]  # Left, Middle, Right buttons
        self.prev_x, self.prev_y = 0, 0  # Previous mouse positions

    def reset(self):
        self.pitch, self.yaw = 0, 0
        self.translation[:] = 0.0, 0.0, 0.0
        self.distance = 0.0

    @property
    def rotation(self):
        Rx = rotation_matrix((1, 0, 0), math.radians(self.pitch))
        Ry = rotation_matrix((0, 1, 0), math.radians(self.yaw))
        return np.dot(Ry, Rx).astype(np.float32)

state = AppState()

# Initialize the PyQt5 GUI and other components
def initialize_components():
    app = QApplication(sys.argv)
    control_panel = ControlPanel()
    control_panel.show()
    return app, control_panel

# Initialize RealSense camera pipeline
def initialize_realsense_pipeline():
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 60)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 60)
    profile = pipeline.start(config)

    align_to = rs.stream.color
    align = rs.align(align_to)
    depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()
    color_intrinsics = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()

    return pipeline, align, depth_scale, color_intrinsics

# Initialize YOLO pose model
def initialize_yolo_model(model_path):
    pose_model = YOLO(model_path)
    pose_model.verbose = False  # Suppress logging
    return pose_model

# Initialize the Deep SORT tracker
def initialize_tracker():
    return DeepSort(max_age=5, n_init=3, nms_max_overlap=1.0, max_cosine_distance=0.2)

# Function to get a valid depth value around a pixel
def get_valid_depth(depth_image, x, y, max_search_radius=5):
    h, w = depth_image.shape
    for r in range(max_search_radius + 1):
        x_min = max(0, x - r)
        x_max = min(w, x + r)
        y_min = max(0, y - r)
        y_max = min(h, y + r)
        search_area = depth_image[y_min:y_max+1, x_min:x_max+1]
        valid_depths = search_area[search_area > 0]
        if valid_depths.size > 0:
            return np.median(valid_depths)  # Use median for robustness
    return 0

# Process YOLO-Pose results and prepare data for tracking
def process_pose_results(pose_results):
    keypoints_data = pose_results[0].keypoints.data.cpu().numpy() if len(pose_results[0].keypoints) > 0 else []
    boxes = pose_results[0].boxes.xyxy.cpu().numpy() if pose_results[0].boxes is not None else []
    confidences = pose_results[0].boxes.conf.cpu().numpy() if pose_results[0].boxes is not None else []
    detections = [
        ([int(x1), int(y1), int(x2) - int(x1), int(y2) - int(y1)], confidences[i], 'person')
        for i, (x1, y1, x2, y2) in enumerate(boxes)
    ]

    return keypoints_data, detections

# Update tracking using Deep SORT
def update_tracker(tracker, detections, color_image):
    tracks = tracker.update_tracks(detections, frame=color_image)
    if len(tracks) == 0:
        print("No tracks found, resetting tracker.")
        tracker = initialize_tracker()  # Reset tracker if no tracks found
    return tracker, tracks

# Function to process keypoints and skeleton
def process_keypoints_and_skeleton(persons_with_ids, depth_image, total_rotation, total_translation, intrinsics, depth_scale):
    keypoints_3d_transformed = []
    skeleton_lines_transformed = []
    general_head_points_transformed = {}

    num_keypoints = 17  # Total number of keypoints

    for track_id, person_data in persons_with_ids:
        # Initialize list with invalid keypoints
        person_kp_3d_transformed = [(0, 0, -1)] * num_keypoints
        person_skeleton_transformed = []

        # Process each keypoint
        for idx in range(len(person_data)):
            kp = person_data[idx]
            x2d, y2d, confidence = kp[:3]
            if confidence > 0.5:
                x2d = int(x2d)
                y2d = int(y2d)

                # Ensure coordinates are within image bounds
                if 0 <= x2d < depth_image.shape[1] and 0 <= y2d < depth_image.shape[0]:
                    # Get valid depth value at the keypoint
                    depth_value = get_valid_depth(depth_image, x2d, y2d)
                    if depth_value == 0:
                        continue  # Skip this keypoint
                    depth_value *= depth_scale  # Convert to meters

                    # Convert to 3D point using RealSense SDK
                    x3d, y3d, z3d = rs.rs2_deproject_pixel_to_point(intrinsics, [x2d, y2d], depth_value)

                    # Apply combined rotation and translation
                    point_3d = np.array([x3d, y3d, z3d])
                    point_3d_transformed = np.dot(total_rotation, point_3d) + total_translation

                    person_kp_3d_transformed[idx] = point_3d_transformed

        # Collect skeleton lines
        for connection in KEYPOINT_CONNECTIONS:
            kp1_idx, kp2_idx = connection
            if kp1_idx < num_keypoints and kp2_idx < num_keypoints:
                kp1 = person_kp_3d_transformed[kp1_idx]
                kp2 = person_kp_3d_transformed[kp2_idx]

                if kp1[2] > 0 and kp2[2] > 0:  # Valid depths
                    person_skeleton_transformed.append((kp1, kp2))

        keypoints_3d_transformed.append(person_kp_3d_transformed)
        skeleton_lines_transformed.append(person_skeleton_transformed)

        # Compute general head point for this person
        general_head_point = compute_general_head_point(
            person_data, depth_image, total_rotation, total_translation, intrinsics, depth_scale, confidence_threshold=0.5
        )
        if general_head_point is not None:
            general_head_points_transformed[track_id] = general_head_point

    return keypoints_3d_transformed, skeleton_lines_transformed, general_head_points_transformed

# Function to render the point cloud
def render_point_cloud(depth_frame, total_rotation, total_translation, intrinsics, keypoints_3d_transformed, skeleton_lines_transformed, general_head_points_transformed, movement_points_transformed, active_movement_type, active_movement_id):
    """Render the point cloud and 3D spheres for keypoints using Pyglet."""
    glBindFramebuffer(GL_FRAMEBUFFER, fbo)
    glViewport(0, 0, 640, 480)  # Match the size to your desired output size

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Set the view using gluLookAt
    gluLookAt(0, 0, 1, 0, 0, 0, 0, 1, 0)
    glEnable(GL_DEPTH_TEST)

    # Draw the point cloud
    verts_transformed = apply_transform(
        np.asanyarray(rs.pointcloud().calculate(depth_frame).get_vertices()).view(np.float32).reshape(-1, 3),
        total_rotation, total_translation
    )
    glBegin(GL_POINTS)
    for x, y, z in verts_transformed:
        if z > 0:
            glVertex3f(x, y, z)
    glEnd()

    # Draw the keypoints as spheres
    for person_kp in keypoints_3d_transformed:
        for x_t, y_t, z_t in person_kp:
            if z_t > 0:
                draw_sphere(x_t, y_t, z_t, radius=0.02)  # Adjust radius for size

    glFlush()

    # Allocate buffer to read the pixels from the framebuffer
    buffer = (GLubyte * (640 * 480 * 3))()  # Buffer for 640x480 RGB image

    # Read the pixels into the buffer
    glReadPixels(0, 0, 640, 480, GL_RGB, GL_UNSIGNED_BYTE, buffer)

    # Create Pyglet ImageData using the buffer
    pyglet_image_data = pyglet.image.ImageData(640, 480, 'RGB', buffer)

    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    return pyglet_image_data

previous_movement_points = {}

def resize_frame_with_aspect_ratio(frame, target_width, target_height):
    h, w = frame.shape[:2]
    aspect_ratio = w / h

    # Calculate new dimensions while maintaining aspect ratio
    if target_width / aspect_ratio <= target_height:
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    else:
        new_height = target_height
        new_width = int(target_height * aspect_ratio)

    # Resize the frame
    resized_frame = cv2.resize(frame, (new_width, new_height))
    return resized_frame, new_width, new_height

def process_frames(pipeline, align, depth_scale, color_intrinsics, pose_model, tracker, control_panel, app):
    # Initialize background subtractor
    previous_head_points = {}
    alpha = 0.8

    cv2.namedWindow("YOLO Pose + Point Cloud", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("YOLO Pose + Point Cloud", mouse_event, param=state)

    try:
        while True:
            # Get frames from RealSense
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)
            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())

            # Flip images for alignment
            color_image = cv2.flip(color_image, 1)
            depth_image = cv2.flip(depth_image, 1)

            # Adjust intrinsics after flipping the image
            flipped_intrinsics = rs.intrinsics()
            flipped_intrinsics.width = color_intrinsics.width
            flipped_intrinsics.height = color_intrinsics.height
            flipped_intrinsics.fx = color_intrinsics.fx
            flipped_intrinsics.fy = color_intrinsics.fy
            flipped_intrinsics.ppx = color_intrinsics.width - color_intrinsics.ppx - 1
            flipped_intrinsics.ppy = color_intrinsics.ppy
            flipped_intrinsics.model = color_intrinsics.model
            flipped_intrinsics.coeffs = color_intrinsics.coeffs

            # Detect movement using background subtraction
            fg_mask, movement_boxes = detect_movement(color_image)

            # Run YOLO pose detection
            pose_results = pose_model(color_image, verbose=False)
            keypoints_data, detections = process_pose_results(pose_results)

            # Update tracker
            tracker, tracks = update_tracker(tracker, detections, color_image)

            # Map track IDs to detection indices
            person_id_to_index = {}
            person_boxes = []
            for track in tracks:
                if not track.is_confirmed():
                    continue
                track_id = track.track_id
                ltrb = track.to_ltrb()
                x1, y1, x2, y2 = map(int, ltrb)

                # Match track to detection
                for idx, det in enumerate(detections):
                    det_box = det[0]
                    det_ltrb = [det_box[0], det_box[1], det_box[0] + det_box[2], det_box[1] + det_box[3]]
                    if bbox_iou(det_ltrb, ltrb) > 0.5:
                        person_id_to_index[track_id] = idx
                        break

                person_boxes.append({'track_id': track_id, 'bbox': (x1, y1, x2, y2)})

            # Compute movement status for each person
            person_moving_status = {}
            for person in person_boxes:
                track_id = person['track_id']
                x1, y1, x2, y2 = person['bbox']
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(color_image.shape[1], x2)
                y2 = min(color_image.shape[0], y2)
                person_fg_mask = fg_mask[y1:y2, x1:x2]
                movement_pixels = cv2.countNonZero(person_fg_mask)
                bbox_area = (x2 - x1) * (y2 - y1)
                movement_ratio = movement_pixels / bbox_area if bbox_area > 0 else 0
                person_moving_status[track_id] = movement_ratio > 0.01

            non_person_movement_boxes = get_non_person_movement_boxes(
                movement_boxes, person_boxes, movement_person_overlap_threshold=0.1
            )

            # Map keypoints onto the point cloud
            rotation_angles = [math.radians(control_panel.rotation_sliders[i].value()) for i in range(3)]
            translation_values = [control_panel.translation_sliders[i].value() / 1000.0 for i in range(3)]
            rotation_matrix_control = get_rotation_matrix(rotation_angles)

            # Combine rotations and translations
            total_rotation = np.dot(state.rotation, rotation_matrix_control)
            total_translation = state.translation + translation_values

            # Process movement points
            movement_points_transformed = compute_movement_points(
                non_person_movement_boxes, depth_image, total_rotation, total_translation,
                flipped_intrinsics, depth_scale, previous_movement_points, alpha=alpha
            )

            # Manually draw the keypoints and skeleton
            draw_keypoints_manually(color_image, keypoints_data)
            draw_skeleton(color_image, keypoints_data)

            # Build a list of (track_id, person_data)
            persons_with_ids = []
            for track_id, idx in person_id_to_index.items():
                if idx < len(keypoints_data):
                    person_data = keypoints_data[idx]
                    persons_with_ids.append((track_id, person_data))

            keypoints_3d_transformed, skeleton_lines_transformed, general_head_points_transformed = process_keypoints_and_skeleton(
                persons_with_ids, depth_image, total_rotation, total_translation, flipped_intrinsics, depth_scale
            )

            active_movement_id, active_movement_type = update_active_movement(
                general_head_points_transformed, person_moving_status, movement_points_transformed,
                image_width=640, image_height=480, intrinsics=flipped_intrinsics
            )

            # Draw bounding boxes for persons and movement
            draw_person_bounding_boxes(tracks, color_image, person_moving_status, active_movement_id, active_movement_type)
            draw_movement_boxes(non_person_movement_boxes, color_image, active_movement_id, active_movement_type)

            # Smooth general head points
            for track_id in list(previous_head_points.keys()):
                if track_id not in general_head_points_transformed:
                    del previous_head_points[track_id]

            for track_id, head_point in general_head_points_transformed.items():
                if track_id in previous_head_points:
                    smoothed_head_point = smooth_head_point(head_point, previous_head_points[track_id], alpha=alpha)
                else:
                    smoothed_head_point = head_point
                general_head_points_transformed[track_id] = smoothed_head_point
                previous_head_points[track_id] = smoothed_head_point

            # Render and display
            pyglet_image_data  = render_point_cloud(
                depth_frame, total_rotation, total_translation, flipped_intrinsics,
                keypoints_3d_transformed, skeleton_lines_transformed, general_head_points_transformed,
                movement_points_transformed,
                active_movement_type, active_movement_id
            )

            pyglet_image = np.frombuffer(pyglet_image_data.get_data(), dtype=np.uint8).reshape(480, 640, 3)
            pyglet_image = cv2.flip(pyglet_image, 0)  # Flip vertically for correct orientation

            # Combine the OpenCV image on the left and Pyglet image on the right
            combined_frame = np.hstack((color_image, pyglet_image))

            # Get the current size of the window
            window_width, window_height = cv2.getWindowImageRect("YOLO Pose + Point Cloud")[2:4]

            # Resize the frame to fit the window while maintaining the aspect ratio
            resized_frame, new_width, new_height = resize_frame_with_aspect_ratio(combined_frame, window_width, window_height)

            # Create a black background (blank canvas) to place the resized frame
            output_frame = np.zeros((window_height, window_width, 3), dtype=np.uint8)

            # Calculate padding to center the resized frame
            x_offset = (window_width - new_width) // 2
            y_offset = (window_height - new_height) // 2

            # Place the resized frame on the black background
            output_frame[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_frame

            # Display the final frame
            cv2.imshow("YOLO Pose + Point Cloud", output_frame)

            # Process PyQt5 events
            app.processEvents()

            # Handle exit

            if cv2.waitKey(1) in (27, ord('q')):  # Exit on 'q' or ESC
                break
    finally:
        pipeline.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app, control_panel = initialize_components()
    pipeline, align, depth_scale, color_intrinsics = initialize_realsense_pipeline()
    pose_model = initialize_yolo_model("yolo/yolo11n-pose.pt")
    tracker = initialize_tracker()

    # Run the main loop to process frames
    process_frames(pipeline, align, depth_scale, color_intrinsics, pose_model, tracker, control_panel, app)
    sys.exit(app.exec_())
