import pyrealsense2 as rs
import cv2
from ultralytics import YOLO
import logging
import numpy as np
from norfair import Tracker, Detection

logging.getLogger("ultralytics").setLevel(logging.WARNING)

# Load YOLOv8 model
model = YOLO("../yolo/best.pt")  # Replace with your custom model path

# Configure Norfair Tracker
tracker = Tracker(distance_function="euclidean", distance_threshold=100)

# Configure RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 60)  # RGB stream
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 60)    # Depth stream

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

        # Mask invalid depth values
        masked_depth = np.where(depth_image == 0, np.max(depth_image), depth_image)

        # Run YOLOv8 inference
        results = model(frame, stream=True)

        detections = []  # Norfair detections list

        for result in results:
            boxes = result.boxes  # Bounding boxes

            for box in boxes:
                # Get bounding box coordinates and confidence
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = box.conf[0].item()  # Confidence
                cls = int(box.cls[0].item())  # Class ID

                # Filter by confidence threshold
                if conf > 0.5:
                    # Compute center point
                    center = np.array([(x1 + x2) / 2, (y1 + y2) / 2])
                    # Compute bounding box width and height
                    width = x2 - x1
                    height = y2 - y1
                    # Add detection with Norfair's Detection format
                    detections.append(
                        Detection(
                            points=center,
                            scores=np.array([conf]),
                            data={"width": width, "height": height}  # Store size information
                        )
                    )

        # Update tracker
        tracked_objects = tracker.update(detections)

        # Draw tracking results and process depth data
        for tracked_object in tracked_objects:
            if hasattr(tracked_object, 'age') and tracked_object.age > 1:
                center = np.array(tracked_object.estimate).flatten()  # Ensure 1D array
                x, y = int(center[0]), int(center[1])  # Extract scalar coordinates

                # Get bounding box size from detection data
                bb_width = tracked_object.last_detection.data["width"]
                bb_height = tracked_object.last_detection.data["height"]

                # Draw bounding box
                color = (0, 255, 0)  # Green
                x1 = int(x - bb_width // 2)
                y1 = int(y - bb_height // 2)
                x2 = int(x + bb_width // 2)
                y2 = int(y + bb_height // 2)

                # Ensure bounding box coordinates are within image dimensions
                x1_clipped = np.clip(x1, 0, depth_image.shape[1] - 1)
                y1_clipped = np.clip(y1, 0, depth_image.shape[0] - 1)
                x2_clipped = np.clip(x2, 0, depth_image.shape[1] - 1)
                y2_clipped = np.clip(y2, 0, depth_image.shape[0] - 1)

                # Extract depth ROI within the bounding box
                depth_roi = masked_depth[y1_clipped:y2_clipped, x1_clipped:x2_clipped]

                # Check if depth_roi is valid
                if depth_roi.size == 0:
                    continue

                # Find the location of the closest depth point (smallest depth value)
                min_depth_index = np.unravel_index(np.argmin(depth_roi), depth_roi.shape)
                closest_y = y1_clipped + min_depth_index[0]
                closest_x = x1_clipped + min_depth_index[1]
                closest_depth = depth_image[closest_y, closest_x]

                # Draw on RGB frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"ID: {tracked_object.id}"
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                cv2.circle(frame, (closest_x, closest_y), 5, (0, 0, 255), -1)
                cv2.putText(frame, f"Depth: {closest_depth:.2f} mm", (closest_x + 10, closest_y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # Display the frame
        cv2.imshow("YOLOv8 + Norfair Tracking | Depth Stream", frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop RealSense pipeline
    pipeline.stop()
    cv2.destroyAllWindows()
