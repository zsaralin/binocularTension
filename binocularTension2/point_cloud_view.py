import cv2
import math
import numpy as np
import pyglet
import pyglet.gl as gl
import pyrealsense2 as rs
def mouse_event(event, x, y, flags, param):
    # Use the param argument to access the state
    state = param
    if event == cv2.EVENT_LBUTTONDOWN:
        state.mouse_btns[0] = True
        state.prev_x, state.prev_y = x, y
    elif event == cv2.EVENT_LBUTTONUP:
        state.mouse_btns[0] = False
    elif event == cv2.EVENT_RBUTTONDOWN:
        state.mouse_btns[2] = True
        state.prev_x, state.prev_y = x, y
    elif event == cv2.EVENT_RBUTTONUP:
        state.mouse_btns[2] = False
    elif event == cv2.EVENT_MOUSEMOVE:
        dx = x - state.prev_x
        dy = y - state.prev_y
        if state.mouse_btns[0]:  # Left button is pressed
            state.yaw -= dx * 0.5
            state.pitch -= dy * 0.5
        if state.mouse_btns[2]:  # Right button is pressed
            state.translation[0] += dx * 0.005
            state.translation[1] -= dy * 0.005
        state.prev_x, state.prev_y = x, y
    elif event == cv2.EVENT_MOUSEWHEEL:
        if flags > 0:
            state.translation[2] += 0.5  # Zoom in
        else:
            state.translation[2] -= 0.5  # Zoom out

def draw_frustum(out, intrinsics, total_rotation, total_translation, color=(128, 128, 128), thickness=1):
    """
   Draw the frustum for the display positioned 2 meters below the RealSense camera,
   with the center of the frustum parallel to the middle of the point cloud.
   """
    h, w = intrinsics.height, intrinsics.width
    fov_x = 2 * math.atan2(w / 2.0, intrinsics.fx)  # Horizontal FOV
    fov_y = 2 * math.atan2(h / 2.0, intrinsics.fy)  # Vertical FOV

    # Define the pyramid corners (in display space, facing forward)
    near_z = 0.5  # Near clipping plane
    far_z = 5.0   # Far clipping plane

    # Corners of the frustum at the far plane
    far_half_width = math.tan(fov_x / 2.0) * far_z
    far_half_height = math.tan(fov_y / 2.0) * far_z

    # Define the 3D points of the frustum (facing forward along the z-axis, no tilt)
    frustum_points = np.array([
        [0, 0, 0],  # Display origin
        [-far_half_width, -far_half_height, far_z],  # Bottom-left corner
        [far_half_width, -far_half_height, far_z],   # Bottom-right corner
        [far_half_width, far_half_height, far_z],    # Top-right corner
        [-far_half_width, far_half_height, far_z]    # Top-left corner
    ], dtype=np.float32)

    # Apply the translation to position the display 2 meters below, but ensure it's aligned parallel to the point cloud center
    display_translation = total_translation + np.array([0.0, -2.0, 0.0])  # Shift 2m down

    # Apply the rotation to the frustum (this ensures the frustum stays aligned forward)
    # This part was key, we rotate it to keep the frustum parallel to the center of the point cloud
    frustum_points_transformed = np.dot(frustum_points, total_rotation.T) + display_translation

    # Project 3D points to 2D using intrinsics
    projected_points = []
    for point in frustum_points_transformed:
        if point[2] > 0:  # Only project points in front of the camera
            u = int((point[0] * intrinsics.fx / point[2]) + intrinsics.ppx)
            v = int((point[1] * intrinsics.fy / point[2]) + intrinsics.ppy)
            projected_points.append((u, v))
        else:
            # If behind the camera, push them out of the visible area
            projected_points.append((-1, -1))

    # Ensure we have at least 5 projected points (origin + 4 corners)
    if len(projected_points) < 5:
        return out  # Not enough points to draw the frustum

    def clip_line(p1, p2):
        """Clip the line at the image boundaries."""
        p1 = (max(0, min(p1[0], w - 1)), max(0, min(p1[1], h - 1)))
        p2 = (max(0, min(p2[0], w - 1)), max(0, min(p2[1], h - 1)))
        return p1, p2

    # Draw the frustum lines for the display
    for i in range(1, 5):
        # Always draw lines from the origin to the corners, and around the frustum base
        origin_to_corner = clip_line(projected_points[0], projected_points[i])
        corner_to_corner = clip_line(projected_points[i], projected_points[i % 4 + 1])

        # Draw lines from the origin (display origin)
        cv2.line(out, origin_to_corner[0], origin_to_corner[1], color, thickness)

        # Draw lines around the frustum base
        cv2.line(out, corner_to_corner[0], corner_to_corner[1], color, thickness)

    return out
def draw_center_frustum(out, intrinsics, center_translation=np.array([0.0, 0.0, 0.0]), rotation_matrix=None, color=(255, 0, 0), thickness=2, rs=None):
    """
    Draw a frustum centered in the middle of the point cloud, facing forward and aligned with the point cloud's center.
    - intrinsics: the camera intrinsics to use for projection.
    - center_translation: position of the frustum in the 3D space (centered by default).
    - rotation_matrix: optional rotation matrix to rotate the frustum if needed.
    - rs: RealSense module, required for deprojecting pixel to 3D points.
    """
    h, w = intrinsics.height, intrinsics.width
    frustum_depth = 5.0  # Frustum length

    # Calculate the frustum corners at a certain depth
    def get_frustum_corner(x, y, z=frustum_depth):
        return rs.rs2_deproject_pixel_to_point(intrinsics, [x, y], z)

    # Get the four corners of the frustum at the far plane
    top_left = np.array(get_frustum_corner(0, 0))
    top_right = np.array(get_frustum_corner(w, 0))
    bottom_right = np.array(get_frustum_corner(w, h))
    bottom_left = np.array(get_frustum_corner(0, h))

    # Apply translation to center the frustum in the 3D space
    top_left += center_translation
    top_right += center_translation
    bottom_right += center_translation
    bottom_left += center_translation

    # Apply rotation if a rotation matrix is provided
    if rotation_matrix is not None:
        top_left = np.dot(rotation_matrix, top_left)
        top_right = np.dot(rotation_matrix, top_right)
        bottom_right = np.dot(rotation_matrix, bottom_right)
        bottom_left = np.dot(rotation_matrix, bottom_left)

    # Project 3D points onto the 2D image using the camera intrinsics
    def project_point(point):
        x, y, z = point
        if z > 0:
            u = int((x * intrinsics.fx / z) + intrinsics.ppx)
            v = int((y * intrinsics.fy / z) + intrinsics.ppy)
            return (u, v)
        return None

    # Project corners onto the 2D image
    corners_2d = [project_point(corner) for corner in [top_left, top_right, bottom_right, bottom_left]]

    # Draw the frustum lines on the 2D image
    for i in range(4):
        if corners_2d[i] is not None and corners_2d[0] is not None:
            cv2.line(out, corners_2d[0], corners_2d[i], color, thickness)  # Line from center to corners

    for i in range(4):
        if corners_2d[i] is not None and corners_2d[(i + 1) % 4] is not None:
            cv2.line(out, corners_2d[i], corners_2d[(i + 1) % 4], color, thickness)  # Connect the corners

    return out