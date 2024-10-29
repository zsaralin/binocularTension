import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from movement_detection.movement_detection import MotionDetector
from rgb_drawing_utils import draw_keypoints_manually, draw_skeleton, bbox_iou
from live_config import LiveConfig
class Detector:
    def __init__(self, model_path="yolo/yolo11n-pose.pt"):
        # Initialize YOLO model for pose detection
        self.pose_model = YOLO(model_path)
        self.tracker = self.initialize_tracker()
        self.motion_detector = MotionDetector()
        self.live_config = LiveConfig.get_instance()

    def initialize_tracker(self):
        """Initialize the Deep SORT tracker"""
        return DeepSort(max_age=5, n_init=3, nms_max_overlap=1.0, max_cosine_distance=0.2)

    def process_pose_results(self, pose_results):
        """Process pose results from YOLO model"""
        keypoints_data = pose_results[0].keypoints.data.cpu().numpy() if len(pose_results[0].keypoints) > 0 else []
        boxes = pose_results[0].boxes.xyxy.cpu().numpy() if pose_results[0].boxes is not None else []
        confidences = pose_results[0].boxes.conf.cpu().numpy() if pose_results[0].boxes is not None else []
        detections = [
            ([int(x1), int(y1), int(x2) - int(x1), int(y2) - int(y1)], confidences[i], 'person')
            for i, (x1, y1, x2, y2) in enumerate(boxes)
        ]
        return keypoints_data, detections

    def update_tracker(self, detections, color_image):
        """Update tracker using detections and return tracked objects"""
        tracks = self.tracker.update_tracks(detections, frame=color_image)
        if len(tracks) == 0:
            print("No tracks found, resetting tracker.")
            self.tracker = self.initialize_tracker()  # Reset tracker if no tracks found
        return tracks

    def detect_movement_and_pose(self, color_image):
        """Run movement detection and pose detection on the color image"""
        # Detect movement using background subtraction
        fg_mask, movement_boxes = self.motion_detector.detect_movement(color_image)

        # Perform YOLO pose detection
        pose_results = self.pose_model(color_image, verbose=False)
        keypoints_data, detections = self.process_pose_results(pose_results)

        # Update tracker
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
                det_ltrb = [det_box[0], det_box[1], det_box[0] + det_box[2], det_box[1] + det_box[3]]
                if bbox_iou(det_ltrb, ltrb) > 0.5:
                    person_id_to_index[track_id] = idx
                    break

            person_boxes.append({'track_id': track_id, 'bbox': (x1, y1, x2, y2)})

        # Compute movement status for each person
        person_moving_status = {}
        for person in person_boxes:
            track_id = person['track_id']
            x1, y1, x2, y2 = person['bbox']
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(color_image.shape[1], x2)
            y2 = min(color_image.shape[0], y2)
            person_fg_mask = fg_mask[y1:y2, x1:x2]
            movement_pixels = cv2.countNonZero(person_fg_mask)
            bbox_area = (x2 - x1) * (y2 - y1)
            movement_ratio = movement_pixels / bbox_area if bbox_area > 0 else 0
            person_moving_status[track_id] = movement_ratio > self.live_config.person_movement_thres

        non_person_movement_boxes = self.motion_detector.get_non_person_movement_boxes(
            movement_boxes, person_boxes, movement_person_overlap_threshold=0.1
        )

        # Build a list of (track_id, person_data)
        persons_with_ids = []
        for track_id, idx in person_id_to_index.items():
            if idx < len(keypoints_data):
                person_data = keypoints_data[idx]
                persons_with_ids.append((track_id, person_data))
        # Return the results
        return tracks, keypoints_data, detections, person_boxes, person_moving_status, non_person_movement_boxes, persons_with_ids
