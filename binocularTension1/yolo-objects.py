import cv2
import numpy as np
import pyrealsense2 as rs
from ultralytics import YOLO

# Load YOLOv8 model (nano version)
model = YOLO('yolov8n.pt')

# Configure RealSense pipeline for depth and color streams
pipeline = rs.pipeline()
config = rs.config()

# Enable the color stream at 640x480 resolution
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

# Create the background subtractor
back_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

# List of class names in YOLOv8
class_names = model.names
exclude_class = 'person'

def does_overlap(person_boxes, x, y, w, h):
    """Check if the moving object's bounding box overlaps with any detected person's box."""
    for (px1, py1, px2, py2) in person_boxes:
        # Check if the current contour box overlaps with any person box
        if x < px2 and (x + w) > px1 and y < py2 and (y + h) > py1:
            return True
    return False

try:
    while True:
        # Get the frames from the RealSense camera
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()

        if not color_frame:
            continue

        # Convert RealSense frame to numpy array
        frame = np.asanyarray(color_frame.get_data())

        # Use YOLOv8 to detect objects (especially people)
        results = model(frame)
        person_boxes = []

        # Extract bounding boxes for detected people
        for result in results:
            for box in result.boxes.data:
                x1, y1, x2, y2, conf, class_idx = box[:6]
                class_name = model.names[int(class_idx)]
                if class_name == exclude_class:  # Store person bounding boxes
                    person_boxes.append((int(x1), int(y1), int(x2), int(y2)))

        # Apply background subtraction to detect moving objects
        fg_mask = back_sub.apply(frame)

        # Find contours in the foreground mask
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Loop over the detected contours (moving objects)
        for contour in contours:
            if cv2.contourArea(contour) > 500:  # Filter out small movements (noise)
                # Get the bounding box of the contour
                x, y, w, h = cv2.boundingRect(contour)

                # Check if the contour overlaps with any person box, if so ignore it
                if not does_overlap(person_boxes, x, y, w, h):
                    # Draw bounding box for detected moving object (not a person)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Display the result
        cv2.imshow('Background Subtraction - Moving Object Detection', frame)
        cv2.imshow('Foreground Mask', fg_mask)

        # Break the loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Release resources
    pipeline.stop()
    cv2.destroyAllWindows()
