import numpy as np 
from ultralytics import YOLO
import logging
from detection_data import DetectionData
import time
import cv2  # Import OpenCV for background subtraction
from live_config import LiveConfig  # Import LiveConfig for dynamic configuration
logging.getLogger("ultralytics").setLevel(logging.WARNING)

# Import DeepSort
from deep_sort_realtime.deepsort_tracker import DeepSort

class ObjectDetector:
    def __init__(self, model_path="./yolo/yolo11n.pt"):
        # Initialize YOLO model
        self.model = YOLO(model_path)
        self.live_config = LiveConfig.get_instance()
        
        # Initialize DeepSort tracker
        self.tracker = DeepSort(
            max_age=30,
            n_init=3,
            max_iou_distance=0.7,
            max_cosine_distance=0.2,
            nms_max_overlap=1.0
        )

        self.detection_data = DetectionData()

        # Initialize variables for tracking missing active movement
        self.person_missing = False
        self.lost_time = None
        self.last_active_bb = None
        self.person_gone = False  # Indicates person has been gone beyond buffer period
        self.last_movement_times = {}
        self.track_buffer_duration = 10  # seconds to keep tracking after movement stops
        # Variables to track active movement duration
        self.active_movement_start_time = None
        self.active_movement_last_seen_time = None
        self.previous_active_movement_id = None

        # Initialize background subtractor
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=25, detectShadows=False
        )
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))  # For morphological operations

    def detect_objects(self, display_image, depth_image, intrinsics, depth_scale):
        active_movement_id = self.detection_data.active_movement_id

        # Check if active movement ID has changed
        if active_movement_id != self.previous_active_movement_id:
            # Active movement ID has changed, reset timers
            self.active_movement_start_time = None
            self.active_movement_last_seen_time = None
            self.previous_active_movement_id = active_movement_id
            self.person_missing = False
            self.person_gone = False

        # Mirror the depth image to match the mirrored display image
        depth_image = np.fliplr(depth_image)

        # Apply background subtraction on the full image
        fg_mask = self.bg_subtractor.apply(display_image)
        # Apply morphological operations to reduce noise
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, self.kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, self.kernel)
        fg_mask = cv2.dilate(fg_mask, self.kernel, iterations=2)

        # Run YOLOv8 inference on the full image
        results = self.model(display_image, stream=True)

        # Determine whether to filter detections to ROI
        filter_to_roi = False
        roi_coords = None
        if self.person_missing:
            time_elapsed = time.time() - self.lost_time
            if time_elapsed < 8 and self.last_active_bb is not None:
                # Only consider detections within ROI
                filter_to_roi = True
                x1 = self.last_active_bb['x1']
                y1 = self.last_active_bb['y1']
                x2 = self.last_active_bb['x2']
                y2 = self.last_active_bb['y2']
                # Optionally expand the bounding box by a margin
                margin = 75  # pixels
                x1 = max(x1 - margin, 0)
                y1 = max(y1 - margin, 0)
                x2 = min(x2 + margin, display_image.shape[1] - 1)
                y2 = min(y2 + margin, display_image.shape[0] - 1)
                roi_coords = (x1, y1, x2, y2)
            else:
                # Time elapsed >= buffer period, reset missing status
                self.person_missing = False
                self.person_gone = True  # Indicate person has been gone beyond buffer period
                self.lost_time = None

        dets = []
        for result in results:
            boxes = result.boxes  # Bounding boxes
            for box in boxes:
                # Get bounding box coordinates and confidence
                x1_box, y1_box, x2_box, y2_box = map(int, box.xyxy[0].tolist())
                conf = box.conf[0].item()  # Confidence
                cls = int(box.cls[0].item())

                # Filter by confidence threshold
                if conf > 0.1:
                    # Optionally filter detections to ROI
                    if filter_to_roi:
                        if not self._is_within_roi(x1_box, y1_box, x2_box, y2_box, roi_coords):
                            continue  # Skip detections outside ROI

                    # Add detection in format required by DeepSort (tlwh)
                    w = x2_box - x1_box
                    h = y2_box - y1_box
                    dets.append([[x1_box, y1_box, w, h], conf, cls])

        # Find background-subtraction contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 200:  # Increased area threshold to reduce noise
                # Get bounding box of the contour
                x, y, w, h = cv2.boundingRect(contour)
                x1_bg = x
                y1_bg = y
                x2_bg = x + w
                y2_bg = y + h

                # Optionally filter detections to ROI
                if filter_to_roi:
                    if not self._is_within_roi(x1_bg, y1_bg, x2_bg, y2_bg, roi_coords):
                        continue  # Skip detections outside ROI

                is_near_yolo = False
                for det in dets:
                    x1_yolo, y1_yolo, w_yolo, h_yolo = det[0]
                    x2_yolo = x1_yolo + w_yolo
                    y2_yolo = y1_yolo + h_yolo
                    # Calculate intersection coordinates
                    xi1 = max(x1_bg, x1_yolo)
                    yi1 = max(y1_bg, y1_yolo)
                    xi2 = min(x2_bg, x2_yolo)
                    yi2 = min(y2_bg, y2_yolo)

                    inter_width = xi2 - xi1
                    inter_height = yi2 - yi1

                    if inter_width > 0 and inter_height > 0:  # There is an intersection
                        inter_area = inter_width * inter_height
                        bg_area = (x2_bg - x1_bg) * (y2_bg - y1_bg)
                        yolo_area = (x2_yolo - x1_yolo) * (y2_yolo - y1_yolo)

                        # Check overlap ratios
                        overlap_with_bg = inter_area / bg_area
                        overlap_with_yolo = inter_area / yolo_area

                        # If fully contained or overlaps significantly, consider it near YOLO
                        is_fully_contained = (
                            x1_bg >= x1_yolo and y1_bg >= y1_yolo and x2_bg <= x2_yolo and y2_bg <= y2_yolo
                        )
                        if is_fully_contained or overlap_with_bg > 0.1 or overlap_with_yolo > 0.1:
                            is_near_yolo = True
                            break

                if not is_near_yolo:
                    # Add background subtraction detection to dets
                    # Using a moderate confidence (e.g., 0.5) and a separate class (e.g., 99)
                    dets.append([[x1_bg, y1_bg, w, h], 0.5, 99])

        # Update DeepSort tracker with combined detections
        tracks = self.tracker.update_tracks(dets, frame=display_image)

        tracked_bbs = []
        found_active_movement = False
        current_time = time.time()

        for track in tracks:
            if not track.is_confirmed() or track.time_since_update > 0:
                continue

            # Extract bounding box coordinates
            x1_tl, y1_tl, w_tl, h_tl = map(int, track.to_tlwh())
            x2_br = x1_tl + w_tl
            y2_br = y1_tl + h_tl

            # Check for movement within the bounding box using the foreground mask
            fg_region = fg_mask[y1_tl:y2_br, x1_tl:x2_br]
            moving_threshold = 100  # Adjust as needed
            is_moving = False
            if fg_region.size > 0 and np.count_nonzero(fg_region) > moving_threshold:
                is_moving = True

            obj_id = track.track_id

            if is_moving:
                # Update the last movement time for this object
                self.last_movement_times[obj_id] = current_time

            # Determine whether to keep tracking this object
            keep_tracking = False
            if is_moving:
                keep_tracking = True
            elif obj_id in self.last_movement_times:
                time_since_movement = current_time - self.last_movement_times[obj_id]
                if time_since_movement <= self.track_buffer_duration:
                    keep_tracking = True
                else:
                    # Remove the object from tracking if buffer duration has passed
                    del self.last_movement_times[obj_id]

            if keep_tracking:
                if obj_id == active_movement_id:
                    found_active_movement = True
                    if self.active_movement_start_time is None:
                        self.active_movement_start_time = current_time
                    self.active_movement_last_seen_time = current_time
                    self.person_missing = False
                    self.person_gone = False

                # Optionally update the last active bounding box
                if obj_id == active_movement_id:
                    self.last_active_bb = {
                        'x1': x1_tl,
                        'y1': y1_tl,
                        'x2': x2_br,
                        'y2': y2_br
                    }

                # Compute the peak depth point
                peak_2d = self._find_peak(depth_image, x1_tl, y1_tl, x2_br, y2_br)

                # Add the tracked object to the output list
                tracked_bbs.append({
                    "id": obj_id,
                    "x1": x1_tl,
                    "y1": y1_tl,
                    "x2": x2_br,
                    "y2": y2_br,
                    "peak": peak_2d,
                    "moving": is_moving
                })

        # Handle disappearance of active movement
        if not found_active_movement:
            if self.active_movement_start_time is not None and self.active_movement_last_seen_time is not None:
                active_duration = self.active_movement_last_seen_time - self.active_movement_start_time
                if active_duration >= 10:  # Changed from 3 to 10 seconds
                    if not self.person_missing and not self.person_gone:
                        # Person just disappeared after being active for at least 10 seconds
                        self.person_missing = True
                        self.lost_time = time.time()
                else:
                    # Active movement was active for less than 10 seconds
                    self.person_missing = False
                    self.person_gone = False
                    self.active_movement_start_time = None
                    self.active_movement_last_seen_time = None
            else:
                # Active movement was not active before
                self.person_missing = False
                self.person_gone = False
                self.active_movement_start_time = None
                self.active_movement_last_seen_time = None
        else:
            # Update last_active_bb if active movement is found
            for bb in tracked_bbs:
                if bb["id"] == active_movement_id:
                    self.last_active_bb = {
                        'x1': bb["x1"],
                        'y1': bb["y1"],
                        'x2': bb["x2"],
                        'y2': bb["y2"]
                    }
                    break

        return tracked_bbs

    def _find_peak(self, depth_image, x1, y1, x2, y2):
        depth_region = depth_image[y1:y2, x1:x2]
        peak_2d = None
        if depth_region.size > 0:
            # Mask invalid depth values (0) with the maximum value in the valid depth region
            max_val = np.max(depth_image) if np.max(depth_image) > 0 else 1
            depth_region_valid = np.where(depth_region == 0, max_val, depth_region)
            min_depth_index = np.unravel_index(np.argmin(depth_region_valid), depth_region.shape)
            y_peak, x_peak = y1 + min_depth_index[0], x1 + min_depth_index[1]
            peak_2d = (x_peak, y_peak)  # 2D peak point in pixel coordinates
        return peak_2d

    def _is_within_roi(self, x1, y1, x2, y2, roi_coords):
        """
        Checks if the bounding box is within the ROI.
        """
        roi_x1, roi_y1, roi_x2, roi_y2 = roi_coords
        # Check if the bounding box is within the ROI
        return (x1 >= roi_x1 and y1 >= roi_y1 and x2 <= roi_x2 and y2 <= roi_y2)
