# Logic for selecting the active movement:
# 1. If `isLooking` is True:
#    a. Check for:
#       - Single moving person → Set as active movement.
#       - Single moving object → Set as active movement.
#       - Multiple moving persons → Choose the closest person.
#       - Multiple moving objects → Choose the closest object.
# 2. If active movement is already set:
#    a. For a person:
#       - Track the person by ID.
#       - If the person temporarily disappears (their ID is no longer detected), 
#         set `waiting_for_return` to True and only look for that specific ID 
#         within the tracked people, giving that person priority if they reappear.
#       - If the timeout exceeds and the person does not return, reset `isLooking` to True.
#    b. For an object:
#       - Track the object by ID.
#       - If the object disappears for more than 5 seconds, reset `isLooking` to True.
# Logic for selecting the active movement:
# 1. If isLooking is True:
#    a. Check for:
#       - Single moving person → Set as active movement.
#       - Single moving object → Set as active movement.
#       - Multiple moving persons → Choose the closest person.
#       - Multiple moving objects → Choose the closest object.
# 2. If active movement is already set:
#    a. For a person:
#       - Track the person by ID.
#       - If the person temporarily disappears (their ID is no longer detected), 
#         set waiting_for_return to True and only look for that specific ID 
#         within the tracked people, giving that person priority if they reappear.
#       - If the timeout exceeds and the person does not return, reset isLooking to True.
#    b. For an object:
#       - Track the object by ID.
#       - If the object disappears for more than 5 seconds, reset isLooking to True.
import time
from select_image import get_image
from live_config import LiveConfig

last_movement_time = time.time()  # Timestamp of the last movement detected for the active movement
isLooking = True  # Represents whether we're looking to set the active movement
last_tracked_time = None  # Timestamp of the last time the active movement was tracked
active_movement = None  # The transformed point of the active movement
active_movement_type = None  # 'person' or 'object'
active_movement_id = None  # ID of the active movement
closest_check_time = time.time()  # Time of the last closest person check

# To track closest person consistency
closest_person_candidate = None  # Temporary closest person candidate
closest_person_frames = 0  # Number of consecutive frames this candidate has been the closest
frames_needed = 2  # Minimum frames needed to confirm a person as the closest
closest_check_interval = 15
def update_active_movement(general_head_points_transformed, person_moving_status, movement_points_transformed, image_width, image_height, intrinsics):
    """Update active movement variables based on both persons and objects."""
    global active_movement, active_movement_type, active_movement_id, isLooking, last_movement_time, last_tracked_time, closest_check_time
    global closest_person_candidate, closest_person_frames, frames_needed
    
    live_config = LiveConfig.get_instance()
    current_time = time.time()
    extended_timeout = live_config.extended_timeout * 60  # Convert minutes to seconds if it's in minutes
    
    moving_persons = {track_id: head_point for track_id, head_point in general_head_points_transformed.items()}
    moving_objects = movement_points_transformed
    if active_movement_id not in moving_persons:
        isLooking = True

    if active_movement_id and (current_time - last_tracked_time >= extended_timeout):
        alternative_persons = {k: v for k, v in moving_persons.items() if k != active_movement_id}
        alternative_objects = {k: v for k, v in moving_objects.items() if k != active_movement_id}

        if alternative_persons:
            active_movement_id, active_movement = min(alternative_persons.items(), key=lambda item: item[1][2])
            active_movement_type = 'person'
            last_movement_time, last_tracked_time = current_time, current_time
        elif alternative_objects:
            active_movement_id, active_movement = min(alternative_objects.items(), key=lambda item: item[1][2])
            active_movement_type = 'object'
            last_movement_time, last_tracked_time = current_time, current_time
        else:
            last_tracked_time = current_time

    if live_config.always_closest and active_movement_type == 'person' and (current_time - closest_check_time >= closest_check_interval):
        closest_check_time = current_time
        min_depth, closest_person_id = -float('inf'), None

        for track_id, head_point in moving_persons.items():
            depth = head_point[2]
            if depth > min_depth:
                min_depth, closest_person_id = depth, track_id

        if closest_person_id is not None and closest_person_id != active_movement_id:
            active_movement_id = closest_person_id
            active_movement = moving_persons[active_movement_id]
            last_movement_time, last_tracked_time = current_time, current_time
    if isLooking or active_movement_type is None:
        if len(moving_persons) == 1 and len(moving_objects) == 0:
            active_movement_id = list(moving_persons.keys())[0]
            active_movement, active_movement_type = moving_persons[active_movement_id], 'person'
            isLooking, last_movement_time, last_tracked_time = False, current_time, current_time

        elif len(moving_persons) == 0 and len(moving_objects) == 1:
            active_movement_id = list(moving_objects.keys())[0]
            active_movement = moving_objects[active_movement_id]
            depth = active_movement[2]  # Get the depth value
            active_movement, active_movement_type = moving_objects[active_movement_id], 'object'
            isLooking, last_movement_time, last_tracked_time = False, current_time, current_time

        elif len(moving_persons) >= 1:
            min_depth, closest_person_id = -float('inf'), None

            for track_id, head_point in moving_persons.items():
                depth = head_point[2]
                if depth > min_depth:
                    min_depth, closest_person_id = depth, track_id

            if closest_person_candidate == closest_person_id:
                closest_person_frames += 1
            else:
                closest_person_candidate, closest_person_frames = closest_person_id, 1
            
            if closest_person_frames >= frames_needed and closest_person_id is not None:
                active_movement_id = closest_person_id
                active_movement, active_movement_type = moving_persons[active_movement_id], 'person'
                isLooking, last_movement_time, last_tracked_time = False, current_time, current_time

        elif len(moving_objects) >= 1:
            min_depth, closest_object_id = -float('inf'), None

            for obj_id, point in moving_objects.items():
                depth = point[2]
                print(depth)
                if depth > min_depth:
                    min_depth, closest_object_id = depth, obj_id

            if closest_object_id is not None:
                active_movement_id = closest_object_id
                active_movement, active_movement_type = moving_objects[active_movement_id], 'object'
                isLooking, last_movement_time, last_tracked_time = False, current_time, current_time

        else:
            if active_movement_type == 'person' and active_movement_id in general_head_points_transformed:
                active_movement = general_head_points_transformed[active_movement_id]
                last_movement_time, last_tracked_time = current_time, current_time
            elif active_movement_type == 'object' and active_movement_id in moving_objects:
                active_movement = moving_objects[active_movement_id]
                last_movement_time = current_time
            else:
                isLooking, active_movement, active_movement_id, active_movement_type = True, None, None, None
    if active_movement is not None:
        x_3d, y_3d, z_3d = active_movement[:3]
        u = (x_3d * intrinsics.fx / z_3d) + intrinsics.ppx
        v = (y_3d * intrinsics.fy / z_3d) + intrinsics.ppy
        u = max(0, min(image_width - int(u) - 1, image_width - 1))
        v = max(0, min(int(v), image_height - 1))
        get_image((x_3d, y_3d, z_3d), image_width, image_height)

    return active_movement_id, active_movement_type
