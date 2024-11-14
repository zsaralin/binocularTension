import pyrealsense2 as rs
import cv2
import numpy as np

# Configure the RealSense pipeline to stream the infrared camera
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.infrared, 640, 480, rs.format.y8, 30)
pipeline.start(config)

# Initialize the background frame as None
bgframe = None

try:
    while True:
        # Capture the infrared frame
        frames = pipeline.wait_for_frames()
        ir_frame = frames.get_infrared_frame()
        if not ir_frame:
            continue

        # Convert the infrared frame to a numpy array
        ir_image = np.asanyarray(ir_frame.get_data())

        # Resize the frame for processing
        ir_image_resized = cv2.resize(ir_image, (600, 500))

        # Convert the infrared image to grayscale (already in grayscale format)
        gray = ir_image_resized

        # Apply Gaussian Blur to reduce sensor noise
        gray = cv2.GaussianBlur(gray, (101, 101), 0)

        # Set the initial background frame
        if bgframe is None:
            bgframe = gray
            continue

        # Compute the difference between the background and current frame
        frameDelta = cv2.absdiff(bgframe, gray)

        # Threshold the delta image to highlight changes (motion)
        _, thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)

        # Dilate the thresholded image to fill in holes and make contours more detectable
        kernel = np.ones((7, 7), np.uint8)
        thresh = cv2.dilate(thresh, kernel, iterations=6)

        # Find contours in the thresholded image
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Filter out small contours to avoid noise
            area = cv2.contourArea(contour)
            if area > 500:
                # Get bounding box coordinates and draw rectangle around detected motion
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(ir_image_resized, (x, y), (x + w, y + h), (255, 0, 255), 3)
                cv2.putText(ir_image_resized, 'MOTION DETECTED', (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Display the resulting frames
        cv2.imshow('Infrared Motion Detection', ir_image_resized)
        cv2.imshow('Threshold', thresh)

        # Press ESC to exit
        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    # Stop streaming and release resources
    pipeline.stop()
    cv2.destroyAllWindows()
