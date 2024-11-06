import pyrealsense2 as rs
import numpy as np
import cv2
import time
from rgb_drawing_utils import bbox_iou
from live_config import LiveConfig  # Import LiveConfig for dynamic configuration

class MotionDetector:
    def __init__(self, buffer=0):
        # Create Background Subtractor MOG2 object
        self.backSub = cv2.createBackgroundSubtractorMOG2()
        self.live_config = LiveConfig.get_instance()

        # List to store tracked objects (bounding box, ID, last seen timestamp)
        self.tracked_objects = []
        self.next_object_id = 1  # Start from ID 1
        self.tracking_hold_duration = self.live_config.tracking_hold_duration  # Hold the bounding box for `bbox_hold_time` seconds after motion stops
        self.buffer = buffer  # Buffer for detecting nearby bounding boxes

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

    def update_tracked_objects(self, detected_bboxes, current_time):
        """
        Update or add tracked objects, maintaining the old ones for the hold time.
        """
        updated_objects = []

        # First, update existing tracked objects with new detections
        for (x, y, w, h) in detected_bboxes:
            updated = False
            for i, (tracked_bbox, obj_id, last_seen) in enumerate(self.tracked_objects):
                # If detected box is near or overlaps with a tracked object, update it
                if self.boxes_near(tracked_bbox, (x, y, w, h)):
                    updated_objects.append(((x, y, w, h), obj_id, current_time))
                    updated = True
                    break

            if not updated:
                # Assign a new ID to the new object
                updated_objects.append(((x, y, w, h), self.next_object_id, current_time))
                self.next_object_id += 1

        # Keep existing objects if they haven't expired yet
        for tracked_bbox, obj_id, last_seen in self.tracked_objects:
            if current_time - last_seen < self.tracking_hold_duration:
                # Retain old boxes until the hold time expires
                if not any(obj_id == updated_obj[1] for updated_obj in updated_objects):
                    updated_objects.append((tracked_bbox, obj_id, last_seen))

        self.tracked_objects = updated_objects
        return updated_objects

    def detect_movement(self, frame):
        """
        Process a color image and return movement boxes with IDs and the foreground mask.
        """
        # Apply background subtraction
        fg_mask = self.backSub.apply(frame)

        # Apply global threshold to remove shadows
        _, mask_thresh = cv2.threshold(fg_mask, 180, 255, cv2.THRESH_BINARY)

        # Set the kernel for morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask_eroded = cv2.morphologyEx(mask_thresh, cv2.MORPH_OPEN, kernel)

        # Retrieve min_contour_area from LiveConfig for dynamic thresholding
        min_contour_area = self.live_config.min_contour_area

        # Find contours of moving objects and filter based on min_contour_area
        contours, _ = cv2.findContours(mask_eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_bboxes = [cv2.boundingRect(cnt) for cnt in contours if cv2.contourArea(cnt) > min_contour_area]

        # Get current time
        current_time = time.time()

        # Update tracked objects with detected bounding boxes, keep old ones for `bbox_hold_time`
        tracked_objects = self.update_tracked_objects(detected_bboxes, current_time)

        # Return the foreground mask and tracked objects (bounding boxes with IDs)
        return fg_mask, tracked_objects

    def get_non_person_movement_boxes(self, tracked_objects, person_boxes, movement_person_overlap_threshold=0.1):
        """
        Return the list of tracked objects that don't overlap with tracked persons.
        """
        non_person_movement_boxes = []

        for tracked_object in tracked_objects:
            # Extract bounding box and ID for the tracked object
            (x1_t, y1_t, w_t, h_t), obj_id, _ = tracked_object
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
                non_person_movement_boxes.append(tracked_object)

        return non_person_movement_boxes
