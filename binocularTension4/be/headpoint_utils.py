import time
import pyrealsense2 as rs
import numpy as np
from transformation_utils import apply_dynamic_transformation
from cube_utils.cube_manager import CubeManager  # Import the singleton instance
from live_config import LiveConfig
from detection_data import DetectionData

previous_movement_points = {}

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
def compute_object_points(tracked_objects, intrinsics, depth_image, depth_scale, rotation, translation, alpha=0.8):
    global previous_movement_points

    def is_valid_depth(x, y, depth_image):
        return 0 <= x < depth_image.shape[1] and 0 <= y < depth_image.shape[0]

    def get_3d_point(x, y, depth_value):
        x3d, y3d, z3d = rs.rs2_deproject_pixel_to_point(intrinsics, [x, y], depth_value)
        point = np.array([x3d, -y3d, -z3d], dtype=np.float32)  # Flip coordinates for consistency
        return point

    def is_within_thresholds(point, thresholds):
        x_min, x_max, y_min, y_max, z_min, z_max = thresholds
        return (
            x_min <= point[0] <= x_max and
            y_min <= point[1] <= y_max and
            z_min <= point[2] <= z_max
        )

    def update_previous_points(obj_id, transformed_point):
        smoothed_point = smooth_point(transformed_point, previous_movement_points.get(obj_id, transformed_point))
        previous_movement_points[obj_id] = smoothed_point
        return smoothed_point

    # Retrieve configuration and thresholds
    live_config = LiveConfig.get_instance()
    thresholds = (
        live_config.x_threshold_min, live_config.x_threshold_max,
        live_config.y_threshold_min, live_config.y_threshold_max,
        live_config.z_threshold_min, live_config.z_threshold_max
    )

    movement_points_transformed = {}
    objects_outside_thresholds = []
    cube_manager = CubeManager.get_instance()

    depth_image = np.fliplr(depth_image)  # Flip depth image horizontally

    for tracked_object in tracked_objects:
        obj_id = tracked_object['id']
        peak = tracked_object.get('peak')

        if not peak:
            continue

        x_peak, y_peak = peak
        if not is_valid_depth(x_peak, y_peak, depth_image):
            continue

        depth_value = depth_image[int(y_peak), int(x_peak)] * depth_scale
        if depth_value <= 0:
            continue

        point_3d = get_3d_point(x_peak, y_peak, depth_value)
        point_3d_transformed = apply_dynamic_transformation([point_3d], rotation, translation)

        if cube_manager.is_point_in_cubes(point_3d_transformed):
            objects_outside_thresholds.append(obj_id)
            continue

        if is_within_thresholds(point_3d_transformed, thresholds):
            movement_points_transformed[obj_id] = update_previous_points(obj_id, point_3d_transformed)
        else:
            objects_outside_thresholds.append(obj_id)

    # Clean up outdated movement points
    previous_movement_points = {
        obj_id: point
        for obj_id, point in previous_movement_points.items()
        if obj_id in movement_points_transformed
    }

    DetectionData().set_objects_outside_thresholds(objects_outside_thresholds)
    return movement_points_transformed
