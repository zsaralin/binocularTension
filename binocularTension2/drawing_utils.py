import cv2

# Define keypoint connections (pairs) to draw skeleton lines
KEYPOINT_CONNECTIONS = [
    (5, 6),   # Shoulders
    (5, 7), (7, 9),  # Left arm (shoulder -> elbow -> wrist)
    (6, 8), (8, 10), # Right arm (shoulder -> elbow -> wrist)
    (11, 12), # Hips
    (5, 11), (6, 12), # Torso (shoulders to hips)
    (11, 13), (13, 15), # Left leg (hip -> knee -> ankle)
    (12, 14), (14, 16)  # Right leg (hip -> knee -> ankle)
]

def draw_person_bounding_boxes(tracks, color_image, person_moving_status, active_movement_id, active_movement_type):
    """Draw bounding boxes around detected people and color them based on movement and active status."""
    for track in tracks:
        if not track.is_confirmed():
            continue
        track_id = track.track_id
        ltrb = track.to_ltrb()
        x1, y1, x2, y2 = map(int, ltrb)

        # Check if this person is the active movement
        if active_movement_type == 'person' and track_id == active_movement_id:
            # If the active person is moving, color green, otherwise magenta
            if person_moving_status.get(track_id, False):
                bbox_color = (0, 255, 0)  # Green for active and moving person
            else:
                bbox_color = (255, 0, 255)  # Magenta for active but not moving person
        else:
            # Choose color based on moving status for non-active persons
            if person_moving_status.get(track_id, False):
                bbox_color = (0, 0, 255)  # Red for moving person
            else:
                bbox_color = (0, 255, 255)  # Yellow for stationary person

        # Draw the bounding box and the track ID
        cv2.rectangle(color_image, (x1, y1), (x2, y2), bbox_color, 2)
        cv2.putText(color_image, f"ID: {track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, bbox_color, 2)

def draw_movement_boxes(non_person_movement_boxes, color_image, active_movement_id, active_movement_type):
    """Draw boxes for the provided tracked objects on the color_image, highlighting the active one."""
    for tracked_object in non_person_movement_boxes:
        (x1_t, y1_t, w_t, h_t), obj_id, _ = tracked_object
        x2_t, y2_t = x1_t + w_t, y1_t + h_t

        # Check if this object is the active movement
        if active_movement_type == 'object' and obj_id == active_movement_id:
            bbox_color = (255, 0, 255)  # Magenta for active object
        else:
            bbox_color = (0, 0, 255)  # Red for other objects

        # Draw the bounding box
        cv2.rectangle(color_image, (x1_t, y1_t), (x2_t, y2_t), bbox_color, 2)
        # Draw the object ID above the box
        cv2.putText(color_image, f"ID: {obj_id}", (x1_t, y1_t - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, bbox_color, 2)

def draw_keypoints_manually(image, keypoints_data, confidence_threshold=0.5):
    """Draw keypoints manually based on the provided format."""
    for person_data in keypoints_data:
        for kp in person_data:  # Each kp should be of the form [x, y, confidence]
            x, y, confidence = kp[:3]
            if confidence > confidence_threshold:
                # Draw a circle at each keypoint
                cv2.circle(image, (int(x), int(y)), 5, (0, 255, 0), -1)


def draw_skeleton(image, keypoints_data, confidence_threshold=0.5):
    """Draw lines (skeleton) connecting keypoints."""
    for person_data in keypoints_data:
        for connection in KEYPOINT_CONNECTIONS:
            kp1_idx, kp2_idx = connection
            if kp1_idx < len(person_data) and kp2_idx < len(person_data):
                x1, y1, c1 = person_data[kp1_idx][:3]
                x2, y2, c2 = person_data[kp2_idx][:3]

                if c1 > confidence_threshold and c2 > confidence_threshold:
                    cv2.line(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)


def bbox_iou(boxA, boxB):
    """Compute the IoU of two bounding boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-5)
    return iou