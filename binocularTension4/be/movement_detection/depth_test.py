import pyrealsense2 as rs
import cv2
import time
import os
import numpy as np

# Configure RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 60)

# Start the pipeline
pipeline.start(config)

# Create a directory to save screenshots
output_dir = "screenshots"
os.makedirs(output_dir, exist_ok=True)

print("Press 'q' to quit.")

try:
    last_capture_time = time.time()
    while True:
        # Wait for a new frame
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue

        # Convert the frame to a NumPy array
        frame = np.asanyarray(color_frame.get_data())

        # Show the live feed
        cv2.imshow("RealSense RGB Camera", frame)

        # Save a screenshot every 5 seconds
        current_time = time.time()
        if current_time - last_capture_time >= 2:
            screenshot_path = os.path.join(output_dir, f"screenshot_{int(current_time)}.jpg")
            cv2.imwrite(screenshot_path, frame)
            print(f"Screenshot saved: {screenshot_path}")
            last_capture_time = current_time

        # Break the loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    # Stop the RealSense pipeline and close OpenCV windows
    pipeline.stop()
    cv2.destroyAllWindows()
