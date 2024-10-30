# Logic for selecting the active movement:
# 1. If `isLooking` is True:
#    a. Check for:
#       - Single moving person → Set as active movement.
#       - Single moving object → Set as active movement.
#       - Multiple moving persons → Choose the closest person.
#       - Multiple moving objects → Choose the closest object.
# 2. If active movement is already set:
#    a. For a person:
#       - Track person by ID.
#       - If person temporarily disappears, wait up to `return_timeout` for them to return.
#       - If timeout exceeds, reset `isLooking` to True.
#    b. For an object:
#       - Track object by ID.
#       - If object disappears for more than 5 seconds, reset `isLooking` to True.

import time
from select_image import get_image

last_movement_time = time.time()  # Timestamp of the last movement detected for the active movement
return_timeout = 1.0  # Timeout in seconds for the person to return
get_image_interval = 0  # Minimum interval between get_image calls in seconds
waiting_for_return = False  # Indicates if we're waiting for the original person to return
isLooking = True  # Represents whether we're looking to set the active movement
last_tracked_time = None  # Timestamp of the last time the active movement was tracked
active_movement = None  # The transformed point of the active movement
active_movement_type = None  # 'person' or 'object'
active_movement_id = None  # ID of the active movement

# Globals to track the last time get_image was called
last_get_image_time = time.time()

# To track closest person consistency
closest_person_candidate = None  # Temporary closest person candidate
closest_person_frames = 0  # Number of consecutive frames this candidate has been the closest
frames_needed = 5  # Minimum frames needed to confirm a person as the closest

def update_active_movement(general_head_points_transformed, person_moving_status, movement_points_transformed, image_width, image_height, intrinsics):
    """Update active movement variables based on both persons and objects."""
    global active_movement, active_movement_type, active_movement_id, isLooking, last_movement_time, last_tracked_time, waiting_for_return
    global last_get_image_time
    global closest_person_candidate, closest_person_frames, frames_needed

    current_time = time.time()
    moving_persons = {track_id: head_point for track_id, head_point in general_head_points_transformed.items() if person_moving_status.get(track_id, False)}
    moving_objects = movement_points_transformed

    # If we are waiting for the original person to return
    if waiting_for_return and active_movement_type == 'person':
        if active_movement_id in general_head_points_transformed:
            active_movement = general_head_points_transformed[active_movement_id]
            last_tracked_time = current_time
            waiting_for_return = False
        elif current_time - last_tracked_time >= return_timeout:
            waiting_for_return = False
            isLooking = True

    if isLooking or active_movement_type is None:

        if len(moving_persons) == 1 and len(moving_objects) == 0:
            active_movement_id = list(moving_persons.keys())[0]
            active_movement, active_movement_type = moving_persons[active_movement_id], 'person'
            isLooking, last_movement_time, last_tracked_time = False, current_time, current_time

        elif len(moving_persons) == 0 and len(moving_objects) == 1:
            active_movement_id = list(moving_objects.keys())[0]
            active_movement, active_movement_type = moving_objects[active_movement_id], 'object'
            isLooking, last_movement_time, last_tracked_time = False, current_time, current_time

        elif len(moving_persons) >= 1:
            min_depth, closest_person_id = float('inf'), None

            for track_id, head_point in moving_persons.items():
                depth = head_point[2]
                if depth > min_depth:
                    min_depth, closest_person_id = depth, track_id

            if closest_person_candidate == closest_person_id:
                closest_person_frames += 1
            else:
                closest_person_candidate, closest_person_frames = closest_person_id, 1

            # Confirm closest if observed for `frames_needed` consecutive frames
            if closest_person_frames >= frames_needed and closest_person_id is not None:
                active_movement_id = closest_person_id
                active_movement, active_movement_type = moving_persons[active_movement_id], 'person'
                isLooking, last_movement_time, last_tracked_time = False, current_time, current_time

        elif len(moving_objects) >= 1:
            min_depth, closest_object_id = float('inf'), None

            for obj_id, point in moving_objects.items():
                depth = point[2]
                if depth < min_depth:
                    min_depth, closest_object_id = depth, obj_id

            if closest_object_id is not None:
                active_movement_id = closest_object_id
                active_movement, active_movement_type = moving_objects[active_movement_id], 'object'
                isLooking, last_movement_time, last_tracked_time = False, current_time, current_time

    else:
        if active_movement_type == 'person':
            if active_movement_id in general_head_points_transformed:
                active_movement = general_head_points_transformed[active_movement_id]
                last_movement_time, last_tracked_time = current_time, current_time
            else:
                waiting_for_return = current_time - last_tracked_time < return_timeout

        elif active_movement_type == 'object':
            if active_movement_id in moving_objects:
                active_movement = moving_objects[active_movement_id]
                last_movement_time = current_time
            elif current_time - last_movement_time >= 2.0:
                isLooking, active_movement, active_movement_id, active_movement_type = True, None, None, None

    if active_movement is not None:
        x_3d, y_3d, z_3d = active_movement[:3]
        u = (x_3d * intrinsics.fx / z_3d) + intrinsics.ppx
        v = (y_3d * intrinsics.fy / z_3d) + intrinsics.ppy
        u = max(0, min(image_width - int(u) - 1, image_width - 1))
        v = max(0, min(int(v), image_height - 1))

        if time.time() - last_get_image_time >= get_image_interval:
            get_image((x_3d, y_3d, z_3d), image_width, image_height)
            last_get_image_time = time.time()

    return active_movement_id, active_movement_type
