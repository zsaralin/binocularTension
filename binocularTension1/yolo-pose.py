import cv2
import torch
from ultralytics import YOLO
import pyrealsense2 as rs
import numpy as np

# Load YOLOv8n-pose model (you can replace this with a larger YOLO model if needed)
model = YOLO('yolo11n-pose.pt')  # Make sure you have the YOLOv8n-pose.pt file
model.verbose = False  # Suppress logging

# Configure RealSense streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)  # Adjust resolution and FPS as needed

# Start streaming
pipeline.start(config)

try:
    while True:
        # Wait for a coherent pair of frames: depth and color
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()

        if not color_frame:
            continue

        # Convert RealSense frame to numpy array (OpenCV image)
        frame = np.asanyarray(color_frame.get_data())

        # Run YOLOv8 pose estimation
        results = model(frame)

        # Plot results (draw keypoints and skeletons on the frame)
        annotated_frame = results[0].plot()  # YOLOv8 automatically draws keypoints

        # Display the frame with keypoints
        cv2.imshow('YOLOv8 Pose Estimation - RealSense', annotated_frame)

        # Exit loop when 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop streaming
    pipeline.stop()

    # Close OpenCV windows
    cv2.destroyAllWindows()
