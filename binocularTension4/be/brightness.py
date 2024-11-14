import pyrealsense2 as rs
import numpy as np
import cv2
import time

# Initialize RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

# Set the interval for calculating brightness (30 seconds)
interval = 5
last_check_time = time.time()

try:
    while True:
        # Capture frames from the camera
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue

        # Convert RealSense frame to numpy array (BGR format for OpenCV)
        frame = np.asanyarray(color_frame.get_data())

        # Display the RGB feed
        cv2.imshow("RealSense RGB Camera", frame)

        # Check if 30 seconds have passed to calculate brightness
        current_time = time.time()
        if current_time - last_check_time >= interval:
            # Convert the frame to grayscale to measure brightness
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            average_brightness = np.mean(gray_frame)
            print(f"Average Brightness: {average_brightness}")

            # Update the time of the last check
            last_check_time = current_time

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    # Stop the pipeline and close OpenCV windows
    pipeline.stop()
    cv2.destroyAllWindows()
