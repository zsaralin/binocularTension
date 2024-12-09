import sys
import math
import numpy as np
import pyrealsense2 as rs
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QHBoxLayout
from transformation_utils import apply_dynamic_transformation
from rgb_drawing_utils import KEYPOINT_CONNECTIONS
from live_config import LiveConfig
from detection_data import DetectionData
import random
from cube_utils.cube_manager import CubeManager
def draw_vertical_dividers(height=2.0, depth=30.0, center_x=0):
    """Draw multiple vertical dividers with evenly spaced x-coordinates."""
    # Access the LiveConfig instance
    live_config = LiveConfig.get_instance()
    num_divisions = live_config.num_divisions  # Total number of divider planes
    camera_z = live_config.camera_z

    # Define the total angle span (-90° to +90°) and calculate even steps
    total_angle_span = live_config.x_divider_angle
  # We want to cover a full 180° field
    angles = [-total_angle_span/2 + i * (total_angle_span / num_divisions) for i in range(num_divisions + 1)]

    for i in range(len(angles) - 1):
        angle1, angle2 = math.radians(angles[i]), math.radians(angles[i + 1])
        
        # Calculate x-coordinates using tangent for wider angles
        x1_far = depth * math.tan(angle1)
        x2_far = depth * math.tan(angle2)
        
        glPushMatrix()
        glTranslatef(center_x, 0, camera_z)
        
        # Draw the first wireframe plane
        glColor3f(0.5, 0.5, 0.5)  # Light gray color for wireframes
        glBegin(GL_LINE_LOOP)
        glVertex3f(0.0, -height / 2, 0.0)
        glVertex3f(0.0, height / 2, 0.0)
        glVertex3f(x1_far, height / 2, -depth)
        glVertex3f(x1_far, -height / 2, -depth)
        glEnd()
        
        # Draw the second wireframe plane
        glBegin(GL_LINE_LOOP)
        glVertex3f(0.0, -height / 2, 0.0)
        glVertex3f(0.0, height / 2, 0.0)
        glVertex3f(x2_far, height / 2, -depth)
        glVertex3f(x2_far, -height / 2, -depth)
        glEnd()
    
        glPopMatrix()
def fill_divider(index_to_fill, height=2.0, depth=30.0, center_x=0):
    """Fill only the space between two adjacent dividers at index_to_fill with a 3D transparent green object."""
    # Access the LiveConfig instance
    live_config = LiveConfig.get_instance()
    x_divider_angle = live_config.x_divider_angle
    num_divisions = live_config.num_divisions  # Use the same `num_divisions` for consistency
    camera_z = live_config.camera_z
    # Define the angle span and calculate even angles as in `draw_vertical_dividers`
    total_angle_span = x_divider_angle
    angles = [-total_angle_span / 2 + i * (total_angle_span / num_divisions) for i in range(num_divisions + 1)]
    
    # Get the two angles that define the space we want to fill
    angle1 = math.radians(angles[index_to_fill])
    angle2 = math.radians(angles[index_to_fill + 1])

    glPushMatrix()
    
    # Enable blending and set transparent green color
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 1.0, 0.0, 0.1)  # Semi-transparent green

    # Disable depth writing for transparency
    glDepthMask(GL_FALSE)

    # Calculate x-coordinates at depth for the specified space
    x1_far = depth * math.tan(angle1) + center_x
    x2_far = depth * math.tan(angle2) + center_x

    # Draw trapezoidal prism for the specified space
    glBegin(GL_QUADS)

    # Front face (near the camera)
    glVertex3f(center_x, -height / 2, camera_z)
    glVertex3f(center_x, height / 2, camera_z)
    glVertex3f(x2_far, height / 2, camera_z - depth)
    glVertex3f(x1_far, -height / 2, camera_z - depth)

    # Back face
    glVertex3f(x1_far, -height / 2, camera_z - depth)
    glVertex3f(x1_far, height / 2, camera_z - depth)
    glVertex3f(x2_far, height / 2, camera_z - depth)
    glVertex3f(x2_far, -height / 2, camera_z - depth)

    # Left side (angle1)
    glVertex3f(center_x, -height / 2, camera_z)
    glVertex3f(center_x, height / 2, camera_z)
    glVertex3f(x1_far, height / 2, camera_z - depth)
    glVertex3f(x1_far, -height / 2, camera_z - depth)

    # Right side (angle2)
    glVertex3f(center_x, -height / 2, camera_z)
    glVertex3f(center_x, height / 2, camera_z)
    glVertex3f(x2_far, height / 2, camera_z - depth)
    glVertex3f(x2_far, -height / 2, camera_z - depth)

    # Top side (between angle1 and angle2)
    glVertex3f(center_x, height / 2, camera_z)
    glVertex3f(x1_far, height / 2, camera_z - depth)
    glVertex3f(x2_far, height / 2, camera_z - depth)
    glVertex3f(center_x, height / 2, camera_z)

    # Bottom side (between angle1 and angle2)
    glVertex3f(center_x, -height / 2, camera_z)
    glVertex3f(x1_far, -height / 2, camera_z - depth)
    glVertex3f(x2_far, -height / 2, camera_z - depth)
    glVertex3f(center_x, -height / 2, camera_z)

    glEnd()

    # Re-enable depth writing after drawing the transparent object
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)
    glPopMatrix()
def draw_horizontal_dividers(camera_y=0, depth=30.0, width=50.0, num_slices=80):
    # Access the LiveConfig instance
    live_config = LiveConfig.get_instance()

    # Get divider values from LiveConfig
    y_top_divider = live_config.y_top_divider
    y_bottom_divider = live_config.y_bottom_divider
    y_top_divider_angle = live_config.y_top_divider_angle
    y_bottom_divider_angle = live_config.y_bottom_divider_angle

    # Calculate the y positions for the planes based on divider values
    dividers = [
        (camera_y + y_top_divider, y_top_divider_angle),  # Top divider with its angle
        (camera_y - y_bottom_divider, y_bottom_divider_angle),  # Bottom divider with its angle
    ]

    # Loop through each divider position and angle to draw the wireframe plane
    for y, angle in dividers:
        glPushMatrix()  # Save the current matrix
        glColor4f(0.5, 0.5, 0.5, 0.5)  # Light gray color with moderate transparency

        # Translate to the starting position of the plane
        glTranslatef(0, y, live_config.camera_z)

        # Apply rotation to tilt the plane
        glRotatef(angle, 1.0, 0.0, 0.0)  # Rotate around the x-axis for tilt

        # Draw the outer border of the plane
        glBegin(GL_LINE_LOOP)
        glVertex3f(-width / 2, 0.0, 0.0)  # Bottom-left corner
        glVertex3f(width / 2, 0.0, 0.0)   # Bottom-right corner
        glVertex3f(width / 2, 0.0, -depth)  # Top-right corner (extending into -z)
        glVertex3f(-width / 2, 0.0, -depth)  # Top-left corner (extending into -z)
        glEnd()

        # Draw the internal grid lines
        glBegin(GL_LINES)
        # Vertical lines (along depth)
        for i in range(num_slices + 1):
            x = -width / 2 + i * (width / num_slices)
            glVertex3f(x, 0.0, 0.0)  # Near edge
            glVertex3f(x, 0.0, -depth)  # Far edge

        glEnd()

        glPopMatrix()  # Restore the previous matrix

def draw_keypoints(persons_with_ids, intrinsics, depth_image, depth_scale, rotation, translation):
    """Draws 3D keypoints as spheres and connects them with 3D lines according to the skeleton structure.
    Sets people outside thresholds in DetectionData for persons with any keypoint out of bounds."""
    
    original_line_width = glGetFloatv(GL_LINE_WIDTH)  # Store the original line width
    glLineWidth(3.0)  # Set thicker line width for skeleton lines
    glEnable(GL_DEPTH_TEST)

    # Access LiveConfig instance for threshold values
    live_config = LiveConfig.get_instance()
    x_min, x_max = live_config.x_threshold_min, live_config.x_threshold_max
    y_min, y_max = live_config.y_threshold_min, live_config.y_threshold_max
    z_min, z_max = live_config.z_threshold_min, live_config.z_threshold_max

    # Array to track people outside thresholds
    people_outside_thresholds = []

    for track_id, person_data in persons_with_ids:
        keypoints_3d_transformed = []
        outside_threshold = False  # Flag to indicate if any keypoint is outside thresholds

        # Process each keypoint in person_data
        for keypoint in person_data:
            x2d, y2d, confidence = keypoint[:3]
            if confidence > 0.5:
                x2d, y2d = int(x2d), int(y2d)

                if 0 <= x2d < depth_image.shape[1] and 0 <= y2d < depth_image.shape[0]:
                    depth_value = depth_image[y2d, -x2d] * depth_scale
                    if depth_value == 0:
                        continue

                    x3d, y3d, z3d = rs.rs2_deproject_pixel_to_point(intrinsics, [x2d, y2d], depth_value)
                    point_3d = np.array([x3d, y3d, z3d], dtype=np.float32)
                    point_3d *= -1  # Invert coordinates for consistency
                    point_3d[0]*= -1
                    point_3d_transformed = apply_dynamic_transformation([point_3d], rotation, translation)
                    cube_manager = CubeManager.get_instance()

                    inside_cube = cube_manager.is_point_in_cubes(point_3d_transformed)
                    within_threshold = (
                        x_min <= point_3d_transformed[0] <= x_max and
                        y_min <= point_3d_transformed[1] <= y_max and
                        z_min <= point_3d_transformed[2] <= z_max
                    )

                    if inside_cube or not within_threshold:
                        outside_threshold = True
                        break
                    else:
                        keypoints_3d_transformed.append(point_3d_transformed)

        # If any keypoint is outside thresholds, mark person and set color to magenta
        if outside_threshold:
            people_outside_thresholds.append(track_id)
            glColor3f(1.0, 0.0, 1.0)  # Magenta for out-of-threshold person
        else:
            glColor3f(1.0, 1.0, 1.0)  # White for keypoints within thresholds

        # Draw each valid keypoint as a sphere
        for point_3d_transformed in keypoints_3d_transformed:
            quadric = gluNewQuadric()
            glPushMatrix()
            glTranslatef(point_3d_transformed[0], point_3d_transformed[1], point_3d_transformed[2])
            gluSphere(quadric, 0.03, 10, 10)
            glPopMatrix()

        # Draw lines between connected keypoints
        glColor3f(1.0, 1.0, 1.0)  # Green for skeleton lines
        glBegin(GL_LINES)
        for kp1_idx, kp2_idx in KEYPOINT_CONNECTIONS:
            if kp1_idx < len(keypoints_3d_transformed) and kp2_idx < len(keypoints_3d_transformed):
                kp1 = keypoints_3d_transformed[kp1_idx]
                kp2 = keypoints_3d_transformed[kp2_idx]
                
                # Only draw if both points have valid Z values to ensure they’re in 3D space
                glVertex3f(kp1[0], kp1[1], kp1[2])
                glVertex3f(kp2[0], kp2[1], kp2[2])
        glEnd()

    # Update DetectionData with people outside thresholds
    DetectionData().set_people_outside_thresholds(people_outside_thresholds)

    glLineWidth(original_line_width)  # Reset line width to its original value


def draw_movement_points(
    transformed_head_points, transformed_movement_points, active_movement_id, active_movement_type
):
    """Draw spheres at the transformed head and movement points in the point cloud with color based on active movement."""

    # Draw head points
    for track_id, head_point in transformed_head_points.items():
        if head_point is None:
            continue  # Skip if the head_point is None

        x_h, y_h, z_h = head_point
        # y_h *= -1
        # z_h *= -1
        # Set color based on active movement status
        if active_movement_type == 'person' and track_id == active_movement_id:
            glColor3f(0.0, 1.0, 0.0)  # Green for active and moving person
        else:
            glColor3f(1,0, 0)  # red for other persons

        # Draw the sphere for the head point
        glPushMatrix()
        glTranslatef(x_h, y_h, z_h)  # Move to the head point's location
        gluSphere(gluNewQuadric(), 0.07, 30, 30)  # Draw a sphere with radius 0.05
        glPopMatrix()
    if transformed_movement_points is None:
        return
    # Draw movement points
    for obj_id, movement_point in transformed_movement_points.items():
        x_m, y_m, z_m = movement_point
        # y_m *= -1
        # z_m *= -1
        # Set color based on active movement status
        if active_movement_type == 'object' and obj_id == active_movement_id:
            glColor3f(0.0, .5, 0)  # dark green for active object
        else:
            glColor3f(1,0, 0)  # red for other objects

        # Draw the sphere for the movement point
        glPushMatrix()
        glTranslatef(x_m, y_m, z_m)  # Move to the movement point's location
        gluSphere(gluNewQuadric(), 0.07, 16, 16)  # Draw a sphere with radius 0.05
        glPopMatrix()