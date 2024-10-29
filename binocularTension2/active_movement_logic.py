import time
from select_filename import get_image

"""
This module tracks active movement (person or object) and dynamically updates it based on motion detected in the scene.
- Active movement is the closest moving person or object.
- If the active person or object stops moving for 5 seconds, it looks for other movement in the scene.
- If no new movement is detected for 5 seconds, the system reverts to the previous active movement.
- The get_image function is rate-limited to a maximum of one call every 30ms to prevent excessive updates.
"""

last_movement_time = time.time()  # Timestamp of the last movement detected for the active movement

return_timeout = 5.0  # Timeout in seconds for the person to return
get_image_interval = 0.1  # Minimum interval between get_image calls in seconds (30 ms)
waiting_for_return = False  # Indicates if we're waiting for the original person to return
isLooking = True  # Represents whether we're looking to set the active movement
last_tracked_time = None  # Timestamp of the last time the active movement was tracked
active_movement = None  # The transformed point of the active movement
active_movement_type = None  # 'person' or 'object'
active_movement_id = None  # ID of the active movement

# Global to track the last time get_image was called
last_get_image_time = time.time()

# Store previous active movement info for potential fallback
previous_active_movement = None
previous_active_movement_type = None
previous_active_movement_id = None

def update_active_movement(general_head_points_transformed, person_moving_status, movement_points_transformed, image_width, image_height, intrinsics):
    """Update active movement variables based on both persons and objects."""
    global active_movement, active_movement_type, active_movement_id, isLooking, last_movement_time, last_tracked_time, waiting_for_return
    global last_get_image_time, previous_active_movement, previous_active_movement_type, previous_active_movement_id

    current_time = time.time()
    moving_persons = {}
    for track_id, is_moving in person_moving_status.items():
        if is_moving and track_id in general_head_points_transformed:
            head_point = general_head_points_transformed[track_id]
            moving_persons[track_id] = head_point

    # Moving objects
    moving_objects = movement_points_transformed

    # If we are waiting for the original person to return
    if waiting_for_return and active_movement_type == 'person':
        if active_movement_id in general_head_points_transformed:
            # The original person returned, resume tracking
            active_movement = general_head_points_transformed[active_movement_id]
            last_tracked_time = current_time
            waiting_for_return = False
        elif current_time - last_tracked_time >= return_timeout:
            # The original person didn't return in time, start looking for new movements
            waiting_for_return = False
            isLooking = True

    if isLooking or active_movement_type is None:
        # Save previous active movement before changing
        previous_active_movement = active_movement
        previous_active_movement_id = active_movement_id
        previous_active_movement_type = active_movement_type

        # Priority: person over object
        if len(moving_persons) == 1 and len(moving_objects) == 0:
            # Only one person moving
            active_movement_id = list(moving_persons.keys())[0]
            active_movement = moving_persons[active_movement_id]
            active_movement_type = 'person'
            isLooking = False
            last_movement_time = current_time
            last_tracked_time = current_time  # Initialize last_tracked_time
        elif len(moving_persons) == 0 and len(moving_objects) == 1:
            # Only one object moving
            active_movement_id = list(moving_objects.keys())[0]
            active_movement = moving_objects[active_movement_id]
            active_movement_type = 'object'
            isLooking = False
            last_movement_time = current_time
            last_tracked_time = current_time
        elif len(moving_persons) >= 1:
            # Multiple people moving, choose the closest one
            min_depth = float('inf')
            closest_person_id = None
            for track_id, head_point in moving_persons.items():
                depth = head_point[2]
                if depth < min_depth:
                    min_depth = depth
                    closest_person_id = track_id
            if closest_person_id is not None:
                active_movement_id = closest_person_id
                active_movement = moving_persons[active_movement_id]
                active_movement_type = 'person'
                isLooking = False
                last_movement_time = current_time
                last_tracked_time = current_time
        elif len(moving_objects) >= 1:
            # Multiple objects moving and no people, choose the closest object
            min_depth = float('inf')
            closest_object_id = None
            for obj_id, point in moving_objects.items():
                depth = point[2]
                if depth < min_depth:
                    min_depth = depth
                    closest_object_id = obj_id
            if closest_object_id is not None:
                active_movement_id = closest_object_id
                active_movement = moving_objects[closest_object_id]
                active_movement_type = 'object'
                isLooking = False
                last_movement_time = current_time
                last_tracked_time = current_time
    else:
        # Continue tracking active movement
        if active_movement_type == 'person':
            if active_movement_id in general_head_points_transformed:
                # Person is still being tracked
                active_movement = general_head_points_transformed[active_movement_id]
                last_movement_time = current_time
                last_tracked_time = current_time
            else:
                # Person is not being tracked, wait for their return
                if current_time - last_tracked_time < return_timeout:
                    waiting_for_return = True
                else:
                    # Reset active movement after timeout
                    isLooking = True
                    active_movement = None
                    active_movement_id = None
                    active_movement_type = None
                    last_movement_time = current_time
                    last_tracked_time = None
        elif active_movement_type == 'object':
            if active_movement_id in moving_objects:
                # Object is still moving
                active_movement = moving_objects[active_movement_id]
                last_movement_time = current_time
            else:
                # Object is not moving
                if current_time - last_movement_time < 5.0:
                    # Wait for 5 seconds before resetting
                    pass
                else:
                    # Reset active movement
                    isLooking = True
                    active_movement = None
                    active_movement_id = None
                    active_movement_type = None
                    last_movement_time = current_time
                    last_tracked_time = None

    # If no new movement detected, revert to the previous active movement
    if active_movement is None and previous_active_movement is not None and (current_time - last_movement_time >= 5):
        active_movement = previous_active_movement
        active_movement_id = previous_active_movement_id
        active_movement_type = previous_active_movement_type

    # Call get_image for active movement if it’s moving
    if active_movement is not None:
        if (active_movement_type == 'person' and person_moving_status.get(active_movement_id, False)) or \
                (active_movement_type == 'object'):
            x_3d, y_3d, z_3d = active_movement[:3]
            # Project 3D point to 2D pixel coordinates
            u = (x_3d * intrinsics.fx / z_3d) + intrinsics.ppx
            v = (y_3d * intrinsics.fy / z_3d) + intrinsics.ppy
            # Adjust for image flip (since the image is flipped horizontally)
            u = image_width - int(u) - 1  # Flip the x-coordinate
            v = int(v)
            # Ensure u and v are within image bounds
            u = max(0, min(u, image_width - 1))
            v = max(0, min(v, image_height - 1))

            # Rate limit get_image calls (minimum interval: 30 ms)
            if time.time() - last_get_image_time >= get_image_interval:
                get_image(u, v, z_3d, image_width, image_height)
                last_get_image_time = time.time()

    return active_movement_id, active_movement_type
