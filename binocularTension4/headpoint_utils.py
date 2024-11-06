import time
import pyrealsense2 as rs
import numpy as np
from transformation_utils import apply_dynamic_transformation
from cube_utils.cube_manager import CubeManager  # Import the singleton instance
from live_config import LiveConfig
from detection_data import DetectionData
# Initialize CubeManager

# Initialize variables to keep track of previous movement points and head points for multiple people
previous_movement_points = {}
previous_head_points = {}
def get_average_depth(depth_image, x, y, depth_scale, window_size=5):
    """Calculate the average depth around a pixel."""
    half_size = window_size // 2
    x_min = max(0, x - half_size)
    x_max = min(depth_image.shape[1], x + half_size + 1)
    y_min = max(0, y - half_size)
    y_max = min(depth_image.shape[0], y + half_size + 1)
    depth_window = depth_image[y_min:y_max, x_min:x_max]
    depth_values = depth_window.flatten()
    valid_depths = depth_values[depth_values > 0]
    if len(valid_depths) == 0:
        return 0  # No valid depth in the window
    return np.mean(valid_depths) * depth_scale

def smooth_point(new_point, previous_point):
    live_config = LiveConfig.get_instance()
    alpha = live_config.headpoint_smoothing
    if previous_point is None:
        return new_point
    if new_point is None:
        return previous_point
    return alpha * previous_point + (1 - alpha) * new_point

def compute_general_head_points(persons_with_ids, intrinsics, depth_image, depth_scale, rotation, translation, confidence_threshold=0.5):
    global previous_head_points
    head_keypoints_indices = [0, 1, 2, 3, 4]
    smoothed_head_points = {}
    live_config = LiveConfig.get_instance()
    x_min, x_max = live_config.x_threshold_min, live_config.x_threshold_max
    y_min, y_max = live_config.y_threshold_min, live_config.y_threshold_max
    z_min, z_max = live_config.z_threshold_min, live_config.z_threshold_max

    for track_id, person_data in persons_with_ids:
        valid_head_points = []
        fallback_point = None
        highest_y = float('inf')

        for idx, kp in enumerate(person_data):
            x2d, y2d, confidence = kp[:3]

            if confidence > confidence_threshold:
                x2d, y2d = int(x2d), int(y2d)

                if 0 <= x2d < depth_image.shape[1] and 0 <= y2d < depth_image.shape[0]:
                    depth_value = depth_image[y2d, -x2d] * depth_scale
                    if depth_value == 0:
                        continue

                    x3d, y3d, z3d = rs.rs2_deproject_pixel_to_point(intrinsics, [x2d, y2d], depth_value)
                    point_3d = np.array([x3d, y3d, z3d], dtype=np.float32)
                    # point_3d[0] *= -1
                    point_3d[1] *= -1
                    point_3d[2] *= -1
                    point_3d_transformed = apply_dynamic_transformation([point_3d], rotation, translation)
                    cube_manager = CubeManager.get_instance()

                    # Exclude point if it's within any cube
                    if cube_manager.is_point_in_cubes(point_3d_transformed):
                        continue
                    elif (x_min <= point_3d_transformed[0] <= x_max and
                        y_min <= point_3d_transformed[1] <= y_max and
                        z_min <= point_3d_transformed[2] <= z_max):
                        if idx in head_keypoints_indices:
                            valid_head_points.append(point_3d_transformed)

                        if y2d < highest_y:
                            highest_y = y2d
                            fallback_point = point_3d_transformed

                        new_head_point = np.mean(valid_head_points, axis=0) if valid_head_points else fallback_point

                        smoothed_head_point = smooth_point(new_head_point, previous_head_points.get(track_id, new_head_point))
                        smoothed_head_points[track_id] = smoothed_head_point
                        previous_head_points[track_id] = smoothed_head_point
    return smoothed_head_points

def compute_movement_points(drawn_objects, intrinsics, depth_image, depth_scale, rotation, translation, alpha=0.8):
    global previous_movement_points
    movement_points_transformed = {}
    live_config = LiveConfig.get_instance()
    x_min, x_max = live_config.x_threshold_min, live_config.x_threshold_max
    y_min, y_max = live_config.y_threshold_min, live_config.y_threshold_max
    z_min, z_max = live_config.z_threshold_min, live_config.z_threshold_max

    # List to keep track of objects outside thresholds
    objects_outside_thresholds = []

    for tracked_object in drawn_objects:
        (x1_t, y1_t, w_t, h_t), obj_id, _ = tracked_object
        x2_t, y2_t = x1_t + w_t, y1_t + h_t

        x_center, y_center = int((x1_t + x2_t) / 2), int((y1_t + y2_t) / 2)

        if 0 <= x_center < intrinsics.width and 0 <= y_center < intrinsics.height:
            depth_value = depth_image[y_center, -x_center] * depth_scale
            if depth_value == 0:
                continue

            x3d, y3d, z3d = rs.rs2_deproject_pixel_to_point(intrinsics, [x_center, y_center], depth_value)
            point_3d = np.array([x3d, y3d, z3d], dtype=np.float32)
            # point_3d[0] *= -1
            point_3d[1] *= -1
            point_3d[2] *= -1
            point_3d_transformed = apply_dynamic_transformation([point_3d], rotation, translation)
            cube_manager = CubeManager.get_instance()

            # Exclude point if it's within any cube
            if cube_manager.is_point_in_cubes(point_3d_transformed):
                objects_outside_thresholds.append(obj_id)
                continue

            # Check if point is within thresholds
            within_thresholds = (
                x_min <= point_3d_transformed[0] <= x_max and
                y_min <= point_3d_transformed[1] <= y_max and
                z_min <= point_3d_transformed[2] <= z_max
            )

            if within_thresholds:
                # Smooth and store the point if it's within thresholds
                smoothed_point = smooth_point(point_3d_transformed, previous_movement_points.get(obj_id, point_3d_transformed))
                movement_points_transformed[obj_id] = smoothed_point
                previous_movement_points[obj_id] = smoothed_point
            else:
                # Otherwise, mark it as outside thresholds
                objects_outside_thresholds.append(obj_id)

    # Remove any objects that were previously tracked but are not in the current frame
    for obj_id in list(previous_movement_points.keys()):
        if obj_id not in movement_points_transformed:
            del previous_movement_points[obj_id]

    # Set objects outside thresholds in DetectionData
    DetectionData().set_objects_outside_thresholds(objects_outside_thresholds)

    return movement_points_transformed