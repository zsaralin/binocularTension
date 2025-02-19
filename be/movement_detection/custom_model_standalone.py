import pyrealsense2 as rs
import numpy as np
import cv2
from roboflow import Roboflow

# Initialize the RoboFlow model
API_KEY = "PfGednJlJMw5JDXfKw9e"
rf = Roboflow(api_key=API_KEY)
model = rf.workspace().project("binocular2").version(1).model

# Configure RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
pipeline.start(config)

try:
    while True:
        # Get frames
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        
        # Convert to numpy array
        color_image = np.asanyarray(color_frame.get_data())

        # Run inference
        predictions = model.predict(color_image, confidence=40, overlap=30).json()

        # Draw bounding boxes
        for pred in predictions['predictions']:
            x, y, w, h = int(pred['x']), int(pred['y']), int(pred['width']), int(pred['height'])
            label = pred['class']
            
            # Draw rectangle
            cv2.rectangle(color_image, (x - w // 2, y - h // 2), (x + w // 2, y + h // 2), (0, 255, 0), 2)
            cv2.putText(color_image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Show image
        cv2.imshow("Detections", color_image)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
