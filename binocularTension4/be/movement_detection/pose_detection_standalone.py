import pyrealsense2 as rs
import numpy as np
import cv2
from ultralytics import YOLO

# Initialize the RealSense camera
pipeline = rs.pipeline()
config = rs.config()
# Enable the color stream (RGB)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start the camera
pipeline.start(config)

# Load the YOLOv8 object detection model
model = YOLO("./yolo/yolo11n.pt")  # Adjust the path to your model file

# Initialize background subtractor
fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=30, detectShadows=True)

try:
    while True:
        # Wait for a coherent color frame
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue

        # Convert the image to a numpy array
        color_image = np.asanyarray(color_frame.get_data())

        # Apply background subtraction to detect motion
        fgmask = fgbg.apply(color_image)
        _, motion_mask = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)

        # Run the YOLOv8 object detection model on the image
        results = model(color_image)

        # Annotate the image with detection results for moving objects only
        for result in results[0].boxes:
            # Extract the bounding box
            box = result.xyxy[0].cpu().numpy().astype(int)  # Convert to NumPy array and cast to int
            conf = result.conf.item()  # Confidence score
            cls = result.cls.item()  # Class index
            label = model.names[int(cls)]  # Class name

            # Extract the region of interest (ROI) from the motion mask
            x_min, y_min, x_max, y_max = box
            x_min, y_min = max(0, x_min), max(0, y_min)
            x_max, y_max = min(color_image.shape[1], x_max), min(color_image.shape[0], y_max)
            roi_motion = motion_mask[y_min:y_max, x_min:x_max]

            # Check if motion is detected in the bounding box
            if np.sum(roi_motion) > 0:  # Motion detected in the ROI
                # Draw the bounding box and label
                cv2.rectangle(color_image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                cv2.putText(
                    color_image,
                    f"{label} {conf:.2f}",
                    (x_min, y_min - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )


        # Display the annotated image
        cv2.imshow("RealSense YOLOv8 Moving Objects", color_image)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    # Stop the camera and close all OpenCV windows
    pipeline.stop()
    cv2.destroyAllWindows()
