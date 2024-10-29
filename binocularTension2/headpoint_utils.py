# headpoint_utils.py
import time

import numpy as np
from transform_utils import apply_transform, convert_depth_pixel_to_metric_coordinate
# Initialize variables to keep track of active movement
def smooth_head_point(new_head_point, previous_head_point, alpha=0.8):
    """Apply exponential moving average to smooth head points."""
    if previous_head_point is None:
        return new_head_point
    return alpha * previous_head_point + (1 - alpha) * new_head_point

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

def compute_general_head_point(person_data, depth_image, rotation_matrix, translation_values, intrinsics, depth_scale, confidence_threshold=0.5):
    """Compute the 3D position of the head keypoints or fallback to the highest keypoint if no head keypoints are available."""
    head_keypoints_indices = [0, 1, 2, 3, 4]  # Nose, Left Eye, Right Eye, Left Ear, Right Ear
    valid_head_points = []
    fallback_point = None
    highest_y = None

    # Loop through all keypoints
    for idx, kp in enumerate(person_data):
        x2d, y2d, confidence = kp[:3]

        if confidence > confidence_threshold:
            x2d = int(x2d)
            y2d = int(y2d)

            # Ensure coordinates are within image bounds
            if 0 <= x2d < depth_image.shape[1] and 0 <= y2d < depth_image.shape[0]:
                # Get average depth around the keypoint
                depth_value = get_average_depth(depth_image, x2d, y2d, depth_scale)

                if depth_value == 0:
                    continue  # Skip if no valid depth

                # Convert to 3D point
                x3d, y3d, z3d = convert_depth_pixel_to_metric_coordinate(depth_value, x2d, y2d, intrinsics)

                # If it's one of the head keypoints, add to the valid head points
                if idx in head_keypoints_indices:
                    valid_head_points.append(np.array([x3d, y3d, z3d]))

                # Track the highest point (fallback) for the case where no head keypoints are available
                if highest_y is None or y2d < highest_y:
                    highest_y = y2d
                    fallback_point = np.array([x3d, y3d, z3d])

    # If we have valid head keypoints, use their average
    if len(valid_head_points) > 0:
        avg_point = np.mean(valid_head_points, axis=0)
        return apply_transform(avg_point.reshape(1, -1), rotation_matrix, translation_values)[0]

    # Otherwise, fall back to the highest detected keypoint
    if fallback_point is not None:
        return apply_transform(fallback_point.reshape(1, -1), rotation_matrix, translation_values)[0]

    return None  # No valid points found

def compute_movement_points(drawn_objects, depth_image, rotation_matrix, translation_values, intrinsics, depth_scale, previous_movement_points, alpha=0.8):
    """Compute the 3D positions of movement midpoints, apply smoothing, and return transformed points."""
    movement_points_transformed = {}
    current_time = time.time()

    for tracked_object in drawn_objects:
        (x1_t, y1_t, w_t, h_t), obj_id, _ = tracked_object
        x2_t, y2_t = x1_t + w_t, y1_t + h_t

        # Compute midpoint of the bounding box
        x_center = int((x1_t + x2_t) / 2)
        y_center = int((y1_t + y2_t) / 2)

        # Ensure coordinates are within image bounds
        if 0 <= x_center < depth_image.shape[1] and 0 <= y_center < depth_image.shape[0]:
            # Get average depth over the bounding box area
            depth_value = get_average_depth(depth_image, x_center, y_center, depth_scale, window_size=5)
            if depth_value == 0:
                continue  # Skip if no valid depth

            # Convert to 3D point
            x3d, y3d, z3d = convert_depth_pixel_to_metric_coordinate(depth_value, x_center, y_center, intrinsics)

            # Apply rotation and translation
            point_3d = np.array([x3d, y3d, z3d])
            point_3d_transformed = apply_transform(point_3d.reshape(1, -1), rotation_matrix, translation_values)[0]

            # Apply smoothing
            if obj_id in previous_movement_points:
                smoothed_point = smooth_head_point(point_3d_transformed, previous_movement_points[obj_id], alpha=alpha)
            else:
                smoothed_point = point_3d_transformed

            movement_points_transformed[obj_id] = smoothed_point
            previous_movement_points[obj_id] = smoothed_point

    # Remove old movement points that are no longer tracked
    for obj_id in list(previous_movement_points.keys()):
        if obj_id not in movement_points_transformed:
            del previous_movement_points[obj_id]

    return movement_points_transformed
