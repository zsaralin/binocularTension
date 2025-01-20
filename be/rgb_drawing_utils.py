import cv2

def draw_bounding_boxes(tracked_objects, color_image, active_movement_id, detection_data):
    for obj in tracked_objects:
        x1, y1, x2, y2 = obj["x1"], obj["y1"], obj["x2"], obj["y2"]
        obj_id = obj["id"]
        is_moving = obj["is_moving"]
        is_yolo = obj["is_yolo"]

        people_outside_thresholds = detection_data.get_objects_outside_thresholds()
        if obj_id in people_outside_thresholds:
            color = (127, 127, 127)  # Grey for people outside thresholds
        elif obj_id == active_movement_id:
            if is_yolo:
                color = (0, 0, 255)  # Bright Red for active movement detected by YOLO
            else:
                color = (0, 0, 150)  # Darker Red for active movement detected by Background Subtraction
        else:
            if is_yolo:
                color = (0, 255, 0)  # Bright Green for YOLO detections
            else:
                color = (0, 150, 0)  # Darker Green for Background Subtraction detections

        label = f"ID: {obj_id}"
        if is_moving:
            # Draw solid bounding box for moving person
            cv2.rectangle(color_image, (x1, y1), (x2, y2), color, 2)
        else:
            # Draw dotted bounding box for stationary person
            for i in range(x1, x2, 15):  # Top edge
                cv2.line(color_image, (i, y1), (min(i + 5, x2), y1), color, 2)
            for i in range(x1, x2, 15):  # Bottom edge
                cv2.line(color_image, (i, y2), (min(i + 5, x2), y2), color, 2)
            for i in range(y1, y2, 15):  # Left edge
                cv2.line(color_image, (x1, i), (x1, min(i + 5, y2)), color, 2)
            for i in range(y1, y2, 15):  # Right edge
                cv2.line(color_image, (x2, i), (x2, min(i + 5, y2)), color, 2)

        cv2.putText(color_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return color_image

def draw_peaks(tracked_objects, color_image,  active_movement_id, detection_data):
    for obj in tracked_objects:
        peak = obj.get("peak")
        obj_id = obj["id"]
        people_outside_thresholds = detection_data.get_objects_outside_thresholds()

        if obj_id in people_outside_thresholds:
            color = (127, 127, 127)  
        elif obj_id == active_movement_id:
            color = (0,0,255)
        else :
            color = (0, 255, 0) 
        if peak:
            x_peak, y_peak = peak
            cv2.circle(color_image, (int(x_peak), int(y_peak)), radius=3, color = color, thickness=-1)

    return color_image
