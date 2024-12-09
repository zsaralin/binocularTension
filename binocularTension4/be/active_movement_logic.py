import time
from select_image import get_image
from live_config import LiveConfig

# Constants
STICK_TIME = 5  # Minimum time (seconds) to stick with the current active movement before switching

# Global variables for tracking state
active_movement_id = None  # ID of the active movement
active_movement = None  # 3D coordinates of the active movement
active_movement_start_time = None  # Time when the current active movement started
potential_switch_start_time = None  # Time when a potential switch to a new movement started
potential_new_active_id = None  # ID of the potential new active movement

def update_active_movement(general_head_points_transformed, image_width, image_height, intrinsics):
    global active_movement_id, active_movement, active_movement_start_time
    global potential_switch_start_time, potential_new_active_id
    current_time = time.time()

    # Reset active movement if no headpoints are provided
    if not general_head_points_transformed:
        active_movement_id = None
        active_movement = None
        active_movement_start_time = None
        potential_switch_start_time = None
        potential_new_active_id = None
        return active_movement_id

    # Find the closest headpoint based on depth
    closest_id, closest_point = max(
        general_head_points_transformed.items(),
        key=lambda item: item[1][2],  # Sort by depth (z-coordinate)
    )

    # If we have an active movement id and it's still in the frame
    if active_movement_id is not None and active_movement_id in general_head_points_transformed:
        # Update active movement position
        active_movement = general_head_points_transformed[active_movement_id]
        
        # Check if there is a new movement that is closer than the current active movement
        current_depth = active_movement[2]
        closest_depth = closest_point[2]
        
        if closest_id != active_movement_id and closest_depth > current_depth:
            # A new movement is closer
            if potential_new_active_id != closest_id:
                # Start timing for potential switch
                potential_new_active_id = closest_id
                potential_switch_start_time = current_time
            else:
                # Check if 'stick_time' has passed
                if current_time - potential_switch_start_time >= STICK_TIME:
                    # Switch to the new movement
                    active_movement_id = potential_new_active_id
                    active_movement = general_head_points_transformed[active_movement_id]
                    active_movement_start_time = current_time
                    # Reset potential switch variables
                    potential_new_active_id = None
                    potential_switch_start_time = None
        else:
            # No new closer movement, reset potential switch variables
            potential_new_active_id = None
            potential_switch_start_time = None

    else:
        # Active movement id is not in the frame
        # Switch immediately to the closest movement
        active_movement_id = closest_id
        active_movement = closest_point
        active_movement_start_time = current_time
        # Reset potential switch variables
        potential_new_active_id = None
        potential_switch_start_time = None

    # Optionally transform the 3D point to 2D for use in UI or processing
    if active_movement is not None:
        x_3d, y_3d, z_3d = active_movement[:3]
        u = int((x_3d * intrinsics.fx / z_3d) + intrinsics.ppx)
        v = int((y_3d * intrinsics.fy / z_3d) + intrinsics.ppy)
        u = max(0, min(image_width - 1, u))  # Ensure the 2D point is within image bounds
        v = max(0, min(image_height - 1, v))
        get_image((x_3d, y_3d, z_3d), image_width, image_height)

    return active_movement_id
