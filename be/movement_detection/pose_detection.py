import cv2
import numpy as np
import time  # Added to handle timing
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from movement_detection.movement_detection import MotionDetector
from live_config import LiveConfig
from detection_data import DetectionData
class Detector:
    def __init__(self, model_path="./yolo/yolo11n-pose.pt"):
        self.pose_model = YOLO(model_path)
        self.tracker = self.initialize_tracker()
        self.motion_detector = MotionDetector()
        self.live_config = LiveConfig.get_instance()
        self.centroid_history = {}
        self.detection_data = DetectionData()
        self.next_even_id = 2
        self.active_id_map = {}  # Map to maintain ID continuity

        # Variables for handling active ID tracking
        self.active_id_last_position = None  # Last known position of the active ID
        self.active_id_disappear_time = None  # Timestamp when the active ID disappeared
        self.search_near_active_only = False  # Whether to restrict detection to the last position area

    def initialize_tracker(self):
        """Initialize the Deep SORT tracker"""
        return DeepSort(max_age=2, n_init=3, nms_max_overlap=0.5, max_cosine_distance=0.2)

    def update_tracker(self, detections, color_image):
        """Update tracker using detections and handle ID reassignment"""
        tracks = self.tracker.update_tracks(detections, frame=color_image)
        updated_tracks = []

        for track in tracks:
            if not track.is_confirmed():
                continue
            updated_tracks.append(track)

        return updated_tracks

    def process_pose_results(self, pose_results):
        """Process pose results from YOLO model"""
        keypoints_data = (
            pose_results[0].keypoints.data.cpu().numpy()
            if len(pose_results[0].keypoints) > 0
            else []
        )
        boxes = (
            pose_results[0].boxes.xyxy.cpu().numpy()
            if pose_results[0].boxes is not None
            else []
        )
        confidences = (
            pose_results[0].boxes.conf.cpu().numpy()
            if pose_results[0].boxes is not None
            else []
        )
        detections = [
            (
                [int(x1), int(y1), int(x2) - int(x1), int(y2) - int(y1)],
                confidences[i],
                'person'
            )
            for i, (x1, y1, x2, y2) in enumerate(boxes)
        ]
        return keypoints_data, detections

    def detect_movement_and_pose(self, color_image):
        """Run movement detection and pose detection on the color image"""

        # Check if pose detection (for people) is enabled and the image is not too dark
        if self.live_config.detect_people and not self.detection_data.get_is_dark():
            # Perform YOLO pose detection
            pose_results = self.pose_model(color_image, verbose=False)
            keypoints_data, detections = self.process_pose_results(pose_results)
        else:
            keypoints_data, detections = [], []

        # Update tracker with detections
        tracks = self.update_tracker(detections, color_image)

        # Map track IDs to detection indices
        person_id_to_index = {}
        person_boxes = []
        for track in tracks:
            if not track.is_confirmed():
                continue
            track_id = track.track_id
            ltrb = track.to_ltrb()
            x1, y1, x2, y2 = map(int, ltrb)

            # Match track to detection
            for idx, det in enumerate(detections):
                det_box = det[0]
                det_ltrb = [
                    det_box[0],
                    det_box[1],
                    det_box[0] + det_box[2],
                    det_box[1] + det_box[3]
                ]
                if bbox_iou(det_ltrb, ltrb) > 0.5:
                    person_id_to_index[track_id] = idx
                    break

            person_boxes.append({'track_id': track_id, 'bbox': (x1, y1, x2, y2)})
        # Handle disappearance and reappearance logic
        tracked_ids = {track.track_id for track in tracks if track.is_confirmed()}
        self.active_id = self.detection_data.active_movement_id
        if self.active_id and self.active_id not in tracked_ids:
            if self.active_id_disappear_time is None:
                # Mark the time when the active ID disappeared
                self.active_id_disappear_time = time.time()
                self.search_near_active_only = True
            elif time.time() - self.active_id_disappear_time > 5:
                # Reset after 15 seconds
                self.active_id = None
                self.active_id_last_position = None
                self.search_near_active_only = False

        # Look for reappearance within the defined radius
        if self.search_near_active_only and self.active_id_last_position:
            x_last, y_last = self.active_id_last_position
            detection_radius = 100  # Define radius for reappearance

            for track in tracks:
                if not track.is_confirmed():
                    continue

                ltrb = track.to_ltrb()
                x1, y1, x2, y2 = map(int, ltrb)
                current_centroid = ((x1 + x2) / 2, (y1 + y2) / 2)

                # Check if the reappeared person is within the radius
                distance_to_last_position = np.linalg.norm(
                    np.array(current_centroid) - np.array([x_last, y_last])
                )
                if distance_to_last_position <= detection_radius:
                    # Map the new track ID to the old active ID
                    self.active_id_map[track.track_id] = self.active_id
                    self.active_id = track.track_id
                    self.detection_data.set_active_movement_id(self.active_id)
                    self.active_id_last_position = current_centroid
                    self.active_id_disappear_time = None
                    self.search_near_active_only = False
                    break

        # Update the last known position of the active ID
        for track in tracks:
            if track.track_id == self.active_id:
                ltrb = track.to_ltrb()
                x1, y1, x2, y2 = map(int, ltrb)
                self.active_id_last_position = ((x1 + x2) / 2, (y1 + y2) / 2)
                break

        # Compute movement status for each person
        person_moving_status = {}
        for person in person_boxes:
            track_id = person['track_id']
            x1, y1, x2, y2 = person['bbox']

            current_centroid = ((x1 + x2) / 2, (y1 + y2) / 2)
            bbox_height = y2 - y1

            previous_centroid = self.centroid_history.get(track_id)
            if previous_centroid:
                movement_distance = np.linalg.norm(
                    np.array(current_centroid) - np.array(previous_centroid)
                )
                normalized_movement = (
                    movement_distance / bbox_height if bbox_height > 0 else movement_distance
                )
                person_moving_status[track_id] = (
                    normalized_movement > self.live_config.person_movement_thres
                )
            else:
                person_moving_status[track_id] = False

            self.centroid_history[track_id] = current_centroid

        # Remove old track IDs from centroid history
        self.centroid_history = {
            track_id: centroid
            for track_id, centroid in self.centroid_history.items()
            if track_id in tracked_ids
        }

        # Check if movement detection (for objects) is enabled
        if self.live_config.detect_objects:
            # Detect non-person movement boxes
            movement_boxes = self.motion_detector.detect_movement(color_image)[1]
            non_person_movement_boxes = self.motion_detector.get_non_person_movement_boxes(
                movement_boxes, person_boxes, movement_person_overlap_threshold=0.1
            )
        else:
            non_person_movement_boxes = []

        # Build a list of (track_id, person_data)
        persons_with_ids = []
        for track_id, idx in person_id_to_index.items():
            if idx < len(keypoints_data):
                person_data = keypoints_data[idx]

                # Check if this track ID was reassigned to the active ID
                if track_id in self.active_id_map:
                    mapped_id = self.active_id_map[track_id]
                else:
                    mapped_id = track_id

                # Add the mapped ID and person data
                persons_with_ids.append((mapped_id, person_data))
        # Return all required values
        return (
            tracks,
            keypoints_data,
            detections,
            person_boxes,
            person_moving_status,
            non_person_movement_boxes,
            persons_with_ids
        )
    