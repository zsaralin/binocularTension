import pyrealsense2 as rs
import numpy as np
import cv2
import time
from live_config import LiveConfig  # Import LiveConfig for dynamic configuration
from detection_data import DetectionData
# Configuration variables
MOG2_HISTORY = 1000
MOG2_VAR_THRESHOLD = 30
THRESHOLD_VALUE = 230
MORPH_KERNEL_SIZE = 3
MERGE_DISTANCE = 50

class MotionDetector:
    def __init__(self, buffer=0):
        # Create Background Subtractor MOG2 object
        self.backSub = cv2.createBackgroundSubtractorMOG2(history=MOG2_HISTORY, varThreshold=MOG2_VAR_THRESHOLD, detectShadows=True)
        self.live_config = LiveConfig.get_instance()

        # List to store tracked objects (bounding box, ID, last seen timestamp)
        self.tracked_objects = {}
        self.next_object_id = 1  # Start from ID 1
        self.buffer = buffer  # Buffer for detecting nearby bounding boxes

        self.detection_data = DetectionData()
        self.active_movement_start_time = None
        self.last_active_area = None  # Store the last known area of active movement

    def boxes_near(self, box1, box2):
        """
        Check if two boxes overlap or are near each other.
        """
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        # Add buffer to allow "near" detection
        if (x1 < x2 + w2 + self.buffer and x1 + w1 + self.buffer > x2 and
                y1 < y2 + h2 + self.buffer and y1 + h1 + self.buffer > y2):
            return True
        return False
    def update_tracked_objects(self, detected_bboxes, current_time, hold_time=0.0):
        """
        Update or add tracked objects, maintaining the old ones for a specified hold time.
        """
        if not detected_bboxes:
            # No detections found, check for expiration of old tracked objects
            expired_objects = [
                obj_id for _, obj_id, last_seen in self.tracked_objects
                if current_time - last_seen > hold_time
            ]
            
            # Remove expired objects
            self.tracked_objects = [
                (bbox, obj_id, last_seen) for bbox, obj_id, last_seen in self.tracked_objects
                if obj_id not in expired_objects
            ]
            
            # Reset object ID if no objects are being tracked
            if not self.tracked_objects:
                self.next_object_id = 1  # Optional: reset object ID counter
            return

        updated_objects = []

        # Update or add new tracked objects
        for (x, y, w, h) in detected_bboxes:
            updated = False
            for i, (tracked_bbox, obj_id, last_seen) in enumerate(self.tracked_objects):
                # Update if the detected box is near or overlaps with a tracked object
                if self.boxes_near(tracked_bbox, (x, y, w, h)):
                    updated_objects.append(((x, y, w, h), obj_id, current_time))
                    updated = True
                    break

            if not updated:
                # Assign a new ID to the new object
                updated_objects.append(((x, y, w, h), self.next_object_id, current_time))
                self.next_object_id += 1

        # Retain existing objects if they haven’t expired
        for tracked_bbox, obj_id, last_seen in self.tracked_objects:
            if obj_id not in [obj[1] for obj in updated_objects] and current_time - last_seen <= hold_time:
                updated_objects.append((tracked_bbox, obj_id, last_seen))

        # Update tracked objects list with updated and retained objects
        self.tracked_objects = updated_objects
    def compute_centroid(self, bbox):
        x, y, w, h = bbox
        return (int(x + w / 2), int(y + h / 2))

    def merge_overlapping_boxes(self, bboxes):
        merged_boxes = []

        while bboxes:
            box = bboxes.pop(0)
            x1, y1, w1, h1 = box
            merged = False

            for i in range(len(merged_boxes)):
                x2, y2, w2, h2 = merged_boxes[i]
                if (x1 < x2 + w2 +MERGE_DISTANCE and x1 + w1 + MERGE_DISTANCE > x2 and
                    y1 < y2 + h2 + MERGE_DISTANCE and y1 + h1 + MERGE_DISTANCE> y2):
                    x_min = min(x1, x2)
                    y_min = min(y1, y2)
                    x_max = max(x1 + w1, x2 + w2)
                    y_max = max(y1 + h1, y2 + h2)
                    merged_boxes[i] = (x_min, y_min, x_max - x_min, y_max - y_min)
                    merged = True
                    break
            
            if not merged:
                merged_boxes.append(box)

        return merged_boxes

    def smooth_bounding_box(self, prev_bbox, new_bbox):
        """Applies exponential smoothing to the bounding box dimensions."""
        alpha = .8
        x1, y1, w1, h1 = prev_bbox
        x2, y2, w2, h2 = new_bbox

        smoothed_x = int(alpha * x2 + (1 - alpha) * x1)
        smoothed_y = int(alpha * y2 + (1 - alpha) * y1)
        smoothed_w = int((alpha/2) * w2 + (1 -(alpha/2)) * w1)
        smoothed_h = int((alpha/2) * h2 + (1 - (alpha/2)) * h1)

        return (smoothed_x, smoothed_y, smoothed_w, smoothed_h)

    def update_tracked_objects(self, detected_bboxes, current_time):
        if not detected_bboxes:
            # No detections found, clear the tracked objects
            self.tracked_objects.clear()
            self.next_object_id = 1  # Optional: reset object ID counter if needed
            return
        new_centroids = []
        for bbox in detected_bboxes:
            centroid = self.compute_centroid(bbox)
            new_centroids.append((bbox, centroid))

        object_ids = list(self.tracked_objects.keys())
        object_centroids = [data['centroid'] for data in self.tracked_objects.values()]

        matches = {}
        unmatched_detections = []

        if len(self.tracked_objects) > 0 and len(new_centroids) > 0:
            D = np.linalg.norm(np.array(object_centroids)[:, np.newaxis] - np.array([c for _, c in new_centroids]), axis=2)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                if D[row, col] > MERGE_DISTANCE:
                    continue

                object_id = object_ids[row]
                prev_bbox = self.tracked_objects[object_id]['bbox']
                new_bbox = new_centroids[col][0]
                
                # Smooth the bounding box update
                smoothed_bbox = self.smooth_bounding_box(prev_bbox, new_bbox)
                
                self.tracked_objects[object_id]['bbox'] = smoothed_bbox
                self.tracked_objects[object_id]['centroid'] = new_centroids[col][1]
                self.tracked_objects[object_id]['last_seen'] = current_time

                matches[object_id] = True
                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(0, D.shape[0])) - used_rows
            for row in unused_rows:
                object_id = object_ids[row]
                del self.tracked_objects[object_id]

            unused_cols = set(range(0, D.shape[1])) - used_cols
            for col in unused_cols:
                unmatched_detections.append(new_centroids[col][0])

        else:
            unmatched_detections = [bbox for bbox, _ in new_centroids]

        for bbox in unmatched_detections:
            self.tracked_objects[self.next_object_id] = {
                'bbox': bbox,
                'centroid': self.compute_centroid(bbox),
                'last_seen': current_time
            }
            self.next_object_id += 1
   
    def update_background_subtractor(self):
            self.backSub = cv2.createBackgroundSubtractorMOG2(
                history=MOG2_HISTORY, 
                varThreshold=MOG2_VAR_THRESHOLD, 
                detectShadows=True
            )
    def detect_movement(self, frame):
        # Fetch the active movement ID from DetectionData
        active_movement_id = self.detection_data.get_active_movement_id()

        # Apply background subtraction to the entire frame
        fg_mask = self.backSub.apply(frame)
        
        # Use threshold and morphology on the mask
        _, mask_thresh = cv2.threshold(fg_mask, THRESHOLD_VALUE, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (MORPH_KERNEL_SIZE, MORPH_KERNEL_SIZE))
        mask_eroded = cv2.morphologyEx(mask_thresh, cv2.MORPH_OPEN, kernel)

        focused_detection = False  # Flag to indicate if we are focusing on a restricted area

        # Only restrict to the last active area when we have an active movement ID
        # print(active_movement_id)
        if active_movement_id is not None:
            # Reset no-active-ID timer and limit detection to the area around active ID
            self.no_active_id_start_time = None
            if active_movement_id in self.tracked_objects:
                x, y, w, h = self.tracked_objects[active_movement_id]['bbox']
                self.last_active_area = (x, y, w, h)  # Update the last active area
                focused_detection = True

                # Define a restricted vertical area around the active ID's x-coordinate
                x_start = max(x - 100, 0)
                x_end = min(x + w + 100, frame.shape[1])
                # Mask out areas outside the focus region
                mask_eroded[:, :x_start] = 0
                mask_eroded[:, x_end:] = 0

        elif self.last_active_area:

            # If no active ID, check last active area for up to 5 seconds before full-frame detection
            if self.no_active_id_start_time is None:
                self.no_active_id_start_time = time.time()  # Start the timer
            elif time.time() - self.no_active_id_start_time < 1:
                focused_detection = True  # Continue checking in the last known area
                x, y, w, h = self.last_active_area
                x_start = max(x - 100, 0)
                x_end = min(x + w + 100, frame.shape[1])
                mask_eroded[:, :x_start] = 0
                mask_eroded[:, x_end:] = 0
            else:
                # Reset after 5 seconds to check the entire frame
                self.last_active_area = None
                self.no_active_id_start_time = None

        # Detect contours within the restricted or full mask area
        contours, _ = cv2.findContours(mask_eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_bboxes = []

        # Collect bounding boxes for contours that meet the area threshold
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            contour_area = cv2.contourArea(cnt)

            if contour_area > self.live_config.min_contour_area:
                detected_bboxes.append((x, y, w, h))

        # Merge overlapping bounding boxes and update tracked objects
        detected_bboxes = self.merge_overlapping_boxes(detected_bboxes)
        current_time = time.time()
        self.update_tracked_objects(detected_bboxes, current_time)

        # Reset the last active area if we have detected new movement without focusing
        if detected_bboxes and not focused_detection:
            self.last_active_area = None

        # Return the processed mask and tracked objects
        return mask_eroded, self.tracked_objects

    def get_non_person_movement_boxes(self, tracked_objects, person_boxes, movement_person_overlap_threshold=0.1):
        """
        Return the list of tracked objects that don't overlap with tracked persons.
        """
        non_person_movement_boxes = []

        for obj_id, tracked_object in tracked_objects.items():
            # Extract bounding box for the tracked object
            x1_t, y1_t, w_t, h_t = tracked_object['bbox']
            x2_t, y2_t = x1_t + w_t, y1_t + h_t

            overlaps_person = False

            # Calculate the center of the tracked object box
            tracked_center_x = (x1_t + x2_t) // 2
            tracked_center_y = (y1_t + y2_t) // 2

            for person in person_boxes:
                x1_p, y1_p, x2_p, y2_p = person['bbox']

                # IoU check
                iou = bbox_iou([x1_p, y1_p, x2_p, y2_p], [x1_t, y1_t, x2_t, y2_t])

                # Pixel-level check
                if (x1_p <= tracked_center_x <= x2_p) and (y1_p <= tracked_center_y <= y2_p):
                    overlaps_person = True
                    break
                elif iou > movement_person_overlap_threshold:
                    overlaps_person = True
                    break

            if not overlaps_person:
                # Include 'id' in the tracked object dictionary
                non_person_movement_boxes.append({
                    'bbox': tracked_object['bbox'],
                    'id': obj_id
                })

        return non_person_movement_boxes