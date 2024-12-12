import pyrealsense2 as rs
import cv2
import numpy as np
from ultralytics import YOLO

# Initialize YOLO model (ensure you have a model trained for 'person' detection)
yolo_model = YOLO("yolo11n-pose.pt")  # Replace with your YOLO model path

# Configure RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
pipeline.start(config)

try:
    while True:
        # Wait for a coherent pair of frames: depth and color
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue

        # Convert images to numpy arrays
        color_image = np.asanyarray(color_frame.get_data())

        # Run YOLO inference
        results = yolo_model(color_image, stream=True)

        # Draw bounding boxes for detected persons
        for result in results:
            boxes = result.boxes  # Bounding boxes
            for box in boxes:
                cls = int(box.cls[0].item())
                conf = box.conf[0].item()
                if cls == 0 and conf > 0.1:  # '0' is typically the 'person' class in COCO dataset
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    # Draw the bounding box and label
                    cv2.rectangle(color_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    label = f"Person {conf:.2f}"
                    cv2.putText(color_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display the resulting frame
        cv2.imshow('RealSense YOLO Detection', color_image)

        # Break the loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop streaming
    pipeline.stop()
    cv2.destroyAllWindows()
