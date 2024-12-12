import numpy as np
from ultralytics import YOLO
from norfair import Tracker, Detection
import logging
from detection_data import DetectionData
import time
import cv2  # Import OpenCV for background subtraction
from live_config import LiveConfig  # Import LiveConfig for dynamic configuration
logging.getLogger("ultralytics").setLevel(logging.WARNING)


class ObjectDetector:
    def __init__(self, model_path="./yolo/yolo11n.pt", distance_threshold=100):
        # Initialize YOLO model
        self.model = YOLO(model_path)
        self.live_config =  LiveConfig.get_instance()
        # Initialize separate Norfair Trackers with increased hit_counter_max
        self.yolo_tracker = Tracker(
            distance_function="euclidean",
            distance_threshold=distance_threshold,
            hit_counter_max=30
        )
        self.bgsub_tracker = Tracker(
            distance_function="euclidean",
            distance_threshold=distance_threshold,
        )
        self.detection_data = DetectionData()

        # Initialize variables for tracking missing active movement
        self.person_missing = False
        self.lost_time = None
        self.last_active_bb = None
        self.person_gone = False  # Indicates person has been gone beyond buffer period

        # Variables to track active movement duration
        self.active_movement_start_time = None
        self.active_movement_last_seen_time = None
        self.previous_active_movement_id = None

        # Initialize background subtractor with adjusted parameters
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=25, detectShadows=False
        )
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))  # For morphological operations

    def detect_objects(self, display_image, depth_image, intrinsics, depth_scale):
        # Initialize movement status dictionary if not already initialized
        if not hasattr(self, 'tracked_objects_movement_status'):
            self.tracked_objects_movement_status = {}
        
        active_movement_id = self.detection_data.active_movement_id
        movement_threshold = self.live_config.movement_thres  # Pixels; adjust based on your application's sensitivity

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
            if time_elapsed < 10 and self.last_active_bb is not None:
                # Only consider detections within ROI
                filter_to_roi = True
                x1 = self.last_active_bb['x1']
                y1 = self.last_active_bb['y1']
                x2 = self.last_active_bb['x2']
                y2 = self.last_active_bb['y2']
                # Optionally expand the bounding box by a margin
                margin = 50  # pixels
                x1 = max(x1 - margin, 0)
                y1 = max(y1 - margin, 0)
                x2 = min(x2 + margin, display_image.shape[1] - 1)
                y2 = min(y2 + margin, display_image.shape[0] - 1)
                roi_coords = (x1, y1, x2, y2)
            else:
                # Time elapsed >= 10 seconds, reset missing status
                self.person_missing = False
                self.person_gone = True  # Indicate person has been gone beyond buffer period
                self.lost_time = None

        yolo_detections = []  # Norfair detections list for YOLO
        yolo_bbs = []  # List to store YOLO bounding boxes for later use
        for result in results:
            boxes = result.boxes  # Bounding boxes

            for box in boxes:
                # Get bounding box coordinates and confidence
                x1_box, y1_box, x2_box, y2_box = map(int, box.xyxy[0].tolist())  # Ensure scalar values

                conf = box.conf[0].item()  # Confidence

                # Filter by confidence threshold
                if conf > 0.1:
                    # Optionally filter detections to ROI
                    if filter_to_roi:
                        if not self._is_within_roi(x1_box, y1_box, x2_box, y2_box, roi_coords):
                            continue  # Skip detections outside ROI

                    # Compute center point
                    center = np.array([(x1_box + x2_box) / 2, (y1_box + y2_box) / 2])
                    # Compute bounding box width and height
                    width = x2_box - x1_box
                    height = y2_box - y1_box
                    # Add detection to Norfair
                    yolo_detections.append(
                        Detection(
                            points=center,
                            scores=np.array([conf]),
                            data={"width": width, "height": height}
                        )
                    )
                    # Store YOLO bounding box for later use
                    yolo_bbs.append((x1_box, y1_box, x2_box, y2_box))

        # Find contours in the foreground mask
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bgsub_detections = []  # Norfair detections list for background subtraction
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Increased area threshold to reduce noise
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
                for x1_yolo, y1_yolo, x2_yolo, y2_yolo in yolo_bbs:
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

                        # Check if bg_bb is fully contained in yolo_bb
                        is_fully_contained = (
                            x1_bg >= x1_yolo and y1_bg >= y1_yolo and x2_bg <= x2_yolo and y2_bg <= y2_yolo
                        )

                        # If fully contained or overlaps significantly, consider it near YOLO
                        if is_fully_contained or overlap_with_bg > 0.1 or overlap_with_yolo > 0.1:
                            is_near_yolo = True
                            break
                if is_near_yolo:
                    continue  # Skip background subtraction detection if near YOLO detection

                # Compute center point
                center = np.array([(x1_bg + x2_bg) / 2, (y1_bg + y2_bg) / 2])
                # Compute bounding box width and height
                width = x2_bg - x1_bg
                height = y2_bg - y1_bg
                # Add detection to Norfair
                bgsub_detections.append(
                    Detection(
                        points=center,
                        scores=np.array([1.0]),  # Assign a default confidence
                        data={"width": width, "height": height}
                    )
                )

        # Update trackers
        yolo_tracked_objects = self.yolo_tracker.update(yolo_detections)
        bgsub_tracked_objects = self.bgsub_tracker.update(bgsub_detections)

        current_time = time.time()

        # Process YOLO tracked objects and update movement status
        for tracked_object in yolo_tracked_objects:
            obj_id = tracked_object.id
            current_position = tracked_object.estimate.copy()  # Position estimate from tracker

            # Initialize movement status if new object
            if obj_id not in self.tracked_objects_movement_status:
                self.tracked_objects_movement_status[obj_id] = {
                    'movement_status': 'stopped',
                    'last_position': current_position,
                    'last_moved_time': current_time,
                    'stopped_time': None
                }
            else:
                # Compute displacement
                last_position = self.tracked_objects_movement_status[obj_id]['last_position']
                displacement = np.linalg.norm(current_position - last_position)
                movement_status = self.tracked_objects_movement_status[obj_id]['movement_status']

                # Modified logic: Object is considered moving only if displacement > movement_threshold AND
                # there is foreground (bg_sub) inside its bounding box.
                if displacement > movement_threshold:
                    # Check fg_mask region inside bounding box
                    x1, y1, x2, y2 = self._get_bounding_box(tracked_object, display_image.shape)
                    fg_region = fg_mask[y1:y2, x1:x2]

                    if np.count_nonzero(fg_region) > 0:
                        # Object is moving
                        self.tracked_objects_movement_status[obj_id]['movement_status'] = 'moving'
                        self.tracked_objects_movement_status[obj_id]['last_moved_time'] = current_time
                        self.tracked_objects_movement_status[obj_id]['stopped_time'] = None
                    else:
                        # No bg_sub indication of movement, treat as if not moving
                        if movement_status == 'moving':
                            # Object has stopped moving
                            self.tracked_objects_movement_status[obj_id]['movement_status'] = 'stationary'
                            self.tracked_objects_movement_status[obj_id]['stopped_time'] = current_time
                        elif movement_status == 'stationary':
                            stopped_time = self.tracked_objects_movement_status[obj_id]['stopped_time']
                            if stopped_time is not None and (current_time - stopped_time) > 20:
                                # Object has been stationary for more than 20 seconds, mark as 'stopped'
                                self.tracked_objects_movement_status[obj_id]['movement_status'] = 'stopped'
                else:
                    # displacement <= movement_threshold
                    if movement_status == 'moving':
                        # Object has stopped moving
                        self.tracked_objects_movement_status[obj_id]['movement_status'] = 'stationary'
                        self.tracked_objects_movement_status[obj_id]['stopped_time'] = current_time
                    elif movement_status == 'stationary':
                        stopped_time = self.tracked_objects_movement_status[obj_id]['stopped_time']
                        if stopped_time is not None and (current_time - stopped_time) > 20:
                            # Object has been stationary for more than 20 seconds, mark as 'stopped'
                            self.tracked_objects_movement_status[obj_id]['movement_status'] = 'stopped'

                # Update last_position
                self.tracked_objects_movement_status[obj_id]['last_position'] = current_position

        tracked_bbs = []
        found_active_movement = False

        # Process YOLO tracked objects based on movement status
        for tracked_object in yolo_tracked_objects:
            obj_id = tracked_object.id
            if obj_id in self.tracked_objects_movement_status:
                movement_status = self.tracked_objects_movement_status[obj_id]['movement_status']
                if movement_status in ['moving', 'stationary']:
                    if tracked_object.age > 1:  # Ensure tracker has stabilized
                        if obj_id == active_movement_id:
                            found_active_movement = True
                            # Update active movement timers
                            if self.active_movement_start_time is None:
                                self.active_movement_start_time = time.time()
                            self.active_movement_last_seen_time = time.time()
                            self.person_missing = False
                            self.person_gone = False
                        self._process_tracked_object(tracked_object, depth_image, tracked_bbs)
                elif movement_status == 'stopped':
                    # Remove the object from the tracker
                    tracked_object.hit_counter = 0  # Mark for deletion

        # Process background subtraction tracked objects as before
        for tracked_object in bgsub_tracked_objects:
            if tracked_object.age > 10:  # Only include stable bgsub objects
                if tracked_object.id == active_movement_id:
                    found_active_movement = True
                    # Update active movement timers
                    if self.active_movement_start_time is None:
                        self.active_movement_start_time = time.time()
                    self.active_movement_last_seen_time = time.time()
                    self.person_missing = False
                    self.person_gone = False
                self._process_tracked_object(tracked_object, depth_image, tracked_bbs)

        # After processing all tracked_objects
        if not found_active_movement:
            if self.active_movement_start_time is not None and self.active_movement_last_seen_time is not None:
                active_duration = self.active_movement_last_seen_time - self.active_movement_start_time
                if active_duration >= 3:
                    if not self.person_missing and not self.person_gone:
                        # Person just disappeared after being active for at least 3 seconds
                        self.person_missing = True
                        self.lost_time = time.time()
                else:
                    # Active movement was active for less than 3 seconds
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
            # Update last_active_bb
            for tracked_object in yolo_tracked_objects + bgsub_tracked_objects:
                if tracked_object.id == active_movement_id:
                    x1, y1, x2, y2 = self._get_bounding_box(tracked_object, depth_image.shape)
                    self.last_active_bb = {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
                    break

        return tracked_bbs


    def _process_tracked_object(self, tracked_object, depth_image, tracked_bbs):
        center = np.array(tracked_object.estimate).flatten()  # Ensure 1D array
        x, y = int(center[0]), int(center[1])  # Extract scalar coordinates

        # Get bounding box size from detection data
        x1, y1, x2, y2 = self._get_bounding_box(tracked_object, depth_image.shape)

        # Extract depth region and handle invalid depth values
        depth_region = depth_image[y1:y2, x1:x2]

        # Find the peak (minimum depth value point)
        peak_2d = None
        if depth_region.size > 0:
            # Mask invalid depth values (0) with the maximum value in the valid depth region
            depth_region_valid = np.where(depth_region == 0, np.max(depth_image), depth_region)

            # Find the closest depth point in the region
            min_depth_index = np.unravel_index(np.argmin(depth_region_valid), depth_region.shape)
            y_peak, x_peak = y1 + min_depth_index[0], x1 + min_depth_index[1]
            peak_2d = (x_peak, y_peak)  # 2D peak point in pixel coordinates

        # Append tracked object info with peak
        tracked_bbs.append({
            "id": tracked_object.id,
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "peak": peak_2d  # 2D peak point
        })

    def _get_bounding_box(self, tracked_object, image_shape):
        center = np.array(tracked_object.estimate).flatten()
        x, y = int(center[0]), int(center[1])

        bb_width = tracked_object.last_detection.data["width"]
        bb_height = tracked_object.last_detection.data["height"]

        x1 = np.clip(int(x - bb_width // 2), 0, image_shape[1] - 1)
        y1 = np.clip(int(y - bb_height // 2), 0, image_shape[0] - 1)
        x2 = np.clip(int(x + bb_width // 2), 0, image_shape[1] - 1)
        y2 = np.clip(int(y + bb_height // 2), 0, image_shape[0] - 1)

        return x1, y1, x2, y2

    def _is_within_roi(self, x1, y1, x2, y2, roi_coords):
        """
        Checks if the bounding box is within the ROI.
        """
        roi_x1, roi_y1, roi_x2, roi_y2 = roi_coords
        # Check if the bounding box is within the ROI
        return (x1 >= roi_x1 and y1 >= roi_y1 and x2 <= roi_x2 and y2 <= roi_y2)
