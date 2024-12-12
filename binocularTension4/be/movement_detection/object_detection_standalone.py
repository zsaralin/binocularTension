import pyrealsense2 as rs 
import cv2
from ultralytics import YOLO
import logging
import numpy as np
from deep_sort_realtime.deepsort_tracker import DeepSort
from collections import defaultdict, deque
import math
import time

logging.getLogger("ultralytics").setLevel(logging.WARNING)

# Load YOLOv8 model
model = YOLO("../yolo/yolo11n.pt")  # Replace with your custom model path

# Initialize DeepSort tracker
tracker = DeepSort(
    max_age=30,
    n_init=3,
    max_iou_distance=0.7,
    max_cosine_distance=0.2,
    nms_max_overlap=1.0
)

# Movement detection parameters
MIN_CONSECUTIVE_MOVEMENT_FRAMES = 5  
MOVEMENT_THRESHOLD = 0.3  # Movement threshold as fraction of object's diagonal
FG_MOVEMENT_THRESHOLD = 0.01  # Fraction of bounding box area that must be foreground
MIN_BG_CONTOUR_AREA = 200  # Minimum area for bg-sub based quick movement to display

# Track movement data: track_id -> {positions: deque, moving_frames: int, is_moving: bool, last_moving_timestamp: float}
track_movement_data = defaultdict(lambda: {
    "positions": deque(maxlen=MIN_CONSECUTIVE_MOVEMENT_FRAMES),
    "moving_frames": 0,
    "is_moving": False,
    "last_moving_timestamp": 0.0
})

# Background subtractor for additional movement check
fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)

# Configure RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 60)  # RGB stream
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 60)   # Depth stream

# Align depth to color
align = rs.align(rs.stream.color)

# Start streaming
pipeline.start(config)

# Get depth scale for converting depth units
depth_sensor = pipeline.get_active_profile().get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print("Depth Scale is: ", depth_scale)

try:
    while True:
        # Capture frames from RealSense camera
        frames = pipeline.wait_for_frames()
        frames = align.process(frames)  # Align depth to color

        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not color_frame or not depth_frame:
            continue

        # Convert frames to numpy arrays
        frame = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())

        # Apply background subtraction
        fgmask = fgbg.apply(frame)

        # Mask invalid depth values
        masked_depth = np.where(depth_image == 0, np.max(depth_image), depth_image)

        # Run YOLOv8 inference
        results = model(frame, stream=True)

        # Prepare detections for DeepSort
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = box.conf[0].item()
                cls = int(box.cls[0].item())

                if conf > 0.1:
                    w = x2 - x1
                    h = y2 - y1
                    detections.append([[x1, y1, w, h], conf, cls])

        # Update DeepSort tracker
        tracks = tracker.update_tracks(detections, frame=frame)

        # Collect track data for later overlap resolution
        moving_candidates = []
        current_ids = set()

        for track in tracks:
            if track.is_confirmed() and track.time_since_update == 0:
                current_ids.add(track.track_id)

                # Get tracked object's bounding box in (x1, y1, x2, y2)
                x1, y1, x2, y2 = track.to_tlbr().astype(int)

                # Compute centroid of the bounding box
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0

                # Update movement data
                data = track_movement_data[track.track_id]
                data["positions"].append((cx, cy))

                # Object size (diagonal)
                w = x2 - x1
                h = y2 - y1
                diag = math.sqrt(w**2 + h**2)
                diag = max(diag, 1e-6)  # Avoid division by zero

                # Compute movement based on displacement
                if len(data["positions"]) > 1:
                    (prev_x, prev_y) = data["positions"][-2]
                    dx = cx - prev_x
                    dy = cy - prev_y
                    dist = math.sqrt(dx**2 + dy**2)

                    movement_limit = diag * MOVEMENT_THRESHOLD
                    if dist > movement_limit:
                        data["moving_frames"] += 1
                    else:
                        data["moving_frames"] = 0

                    is_displacement_moving = data["moving_frames"] >= MIN_CONSECUTIVE_MOVEMENT_FRAMES
                else:
                    is_displacement_moving = False

                # Ensure bounding box is within image dimensions
                x1_clipped = np.clip(x1, 0, depth_image.shape[1]-1)
                y1_clipped = np.clip(y1, 0, depth_image.shape[0]-1)
                x2_clipped = np.clip(x2, 0, depth_image.shape[1]-1)
                y2_clipped = np.clip(y2, 0, depth_image.shape[0]-1)

                # Extract depth ROI within the bounding box
                depth_roi = masked_depth[y1_clipped:y2_clipped, x1_clipped:x2_clipped]

                if depth_roi.size == 0:
                    continue

                # Background subtraction check inside bounding box
                fg_roi = fgmask[y1_clipped:y2_clipped, x1_clipped:x2_clipped]
                total_pixels = fg_roi.size
                fg_count = np.count_nonzero(fg_roi)
                bg_movement_detected = (fg_count / total_pixels) > FG_MOVEMENT_THRESHOLD

                # Mark candidates
                data["candidate_moving"] = is_displacement_moving or bg_movement_detected

                moving_candidates.append((track.track_id, x1, y1, x2, y2, data["candidate_moving"]))

        # Resolve overlapping movement issues
        def boxes_overlap(b1, b2):
            return not (b1[2] < b2[0] or b1[0] > b2[2] or b1[3] < b2[1] or b1[1] > b2[3])

        # Group overlapping tracks
        groups = []
        used = set()
        for i, (tid1, x11, y11, x12, y12, c1) in enumerate(moving_candidates):
            if tid1 in used:
                continue
            group = [(tid1, x11, y11, x12, y12, c1)]
            for j, (tid2, x21, y21, x22, y22, c2) in enumerate(moving_candidates[i+1:], start=i+1):
                if tid2 not in used:
                    if boxes_overlap((x11, y11, x12, y12), (x21, y21, x22, y22)):
                        group.append((tid2, x21, y21, x22, y22, c2))
            for g in group:
                used.add(g[0])
            groups.append(group)

        # Resolve each group
        for group in groups:
            moving_in_group = [g for g in group if g[-1] == True]
            if len(moving_in_group) <= 1:
                # Just set their is_moving to candidate_moving as is
                for (tid, _, _, _, _, candidate) in group:
                    track_movement_data[tid]["is_moving"] = candidate
                    if candidate:
                        track_movement_data[tid]["last_moving_timestamp"] = time.time()
                continue

            # Multiple objects show candidate_moving, pick one
            best_tid = None
            best_time = -1
            for (tid, _, _, _, _, _) in moving_in_group:
                last_time = track_movement_data[tid]["last_moving_timestamp"]
                if last_time > best_time:
                    best_time = last_time
                    best_tid = tid

            if best_tid is None or best_time == 0:
                # Check displacement movers
                displacement_movers = []
                for (tid, _, _, _, _, candidate) in moving_in_group:
                    # Check if displacement was true at this frame
                    if track_movement_data[tid]["moving_frames"] >= MIN_CONSECUTIVE_MOVEMENT_FRAMES:
                        displacement_movers.append(tid)
                if len(displacement_movers) > 0:
                    best_tid = displacement_movers[0]
                else:
                    best_tid = moving_in_group[0][0]

            # Set chosen one to moving, others not
            for (tid, _, _, _, _, candidate) in group:
                if tid == best_tid:
                    track_movement_data[tid]["is_moving"] = True
                    track_movement_data[tid]["last_moving_timestamp"] = time.time()
                else:
                    track_movement_data[tid]["is_moving"] = False

        # Draw tracked objects
        tracked_boxes = []
        for track in tracks:
            if track.is_confirmed() and track.time_since_update == 0:
                tid = track.track_id
                x1, y1, x2, y2 = track.to_tlbr().astype(int)
                data = track_movement_data[tid]
                color = (0, 255, 0)  # Green if not moving
                if data["is_moving"]:
                    color = (0, 0, 255)  # Red if moving
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"ID: {tid}{' (Moving)' if data['is_moving'] else ''}"
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                tracked_boxes.append((x1, y1, x2, y2))

        # Clean up old track data
        for tid in list(track_movement_data.keys()):
            if tid not in current_ids:
                del track_movement_data[tid]

        # Detect and draw background-subtraction-only movement not overlapping objects
        # Find contours in fgmask
        contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < MIN_BG_CONTOUR_AREA:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            contour_box = (x, y, x+w, y+h)
            # Check if overlaps with any tracked box
            overlaps = any(boxes_overlap(contour_box, tb) for tb in tracked_boxes)
            if not overlaps:
                # Draw this as a quick background-sub movement
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 0), 2)
                cv2.putText(frame, "BG Movement", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

        # Display the frame
        cv2.imshow("YOLOv8 + DeepSort | Depth Stream | Movement Detection + BG Sub", frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop RealSense pipeline
    pipeline.stop()
    cv2.destroyAllWindows()
