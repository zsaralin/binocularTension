import cv2
import pyrealsense2 as rs
import numpy as np

# Configure the RealSense pipeline to stream both color and depth frames
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# Start the RealSense pipeline
pipeline.start(config)

# Initialize the first frame as None
previous_frame = None

# Set minimum contour area and movement threshold
min_contour_area = 500  # Minimum area to consider (adjust as needed)
movement_threshold = 50  # Minimum pixel difference to consider as movement

# Get the intrinsics of the color camera
profile = pipeline.get_active_profile()
color_profile = rs.video_stream_profile(profile.get_stream(rs.stream.color))
color_intrinsics = color_profile.get_intrinsics()

try:
    while True:
        # Wait for a coherent set of frames
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        # Check if frames are available
        if not color_frame or not depth_frame:
            continue

        # Convert the RealSense frames to numpy arrays
        current_frame = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())

        # Convert to grayscale for processing
        gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

        # Blur the grayscale image to reduce noise and improve motion detection
        gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

        # If this is the first frame, set it as previous and continue
        if previous_frame is None:
            previous_frame = gray_frame
            continue

        # Compute the absolute difference between the current frame and previous frame
        frame_delta = cv2.absdiff(previous_frame, gray_frame)

        # Apply threshold to highlight significant changes
        _, thresh = cv2.threshold(frame_delta, movement_threshold, 255, cv2.THRESH_BINARY)

        # Optional: Dilate the thresholded image to fill in gaps
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Find contours of the regions with significant motion
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Initialize variables to store the closest movement to the center
        closest_movement = None
        min_distance = float('inf')
        frame_center = (current_frame.shape[1] // 2, current_frame.shape[0] // 2)

        for contour in contours:
            if cv2.contourArea(contour) < min_contour_area:  # Ignore small contours
                continue
            
            (x, y, w, h) = cv2.boundingRect(contour)
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Calculate distance from the center of the frame
            distance = np.sqrt((center_x - frame_center[0])**2 + (center_y - frame_center[1])**2)
            
            if distance < min_distance:
                min_distance = distance
                closest_movement = (x, y, w, h)
                

        # If a movement is detected, draw the rectangle and print coordinates
        if closest_movement is not None:
            (x, y, w, h) = closest_movement
            cv2.rectangle(current_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Get the depth of the center of the detected movement
            center_x = x + w // 2
            center_y = y + h // 2
            depth = depth_frame.get_distance(center_x, center_y)
            
            # Convert from image coordinates to 3D coordinates
            point_3d = rs.rs2_deproject_pixel_to_point(color_intrinsics, [center_x, center_y], depth)
            
            print(f"Movement detected at X: {point_3d[0]:.3f}m, Y: {point_3d[1]:.3f}m, Z: {point_3d[2]:.3f}m")

        # Display the motion detection result and the thresholded frame
        cv2.imshow("Motion Detection - RealSense", current_frame)
        cv2.imshow("Threshold - RealSense", thresh)

        # Update the previous frame for the next iteration
        previous_frame = gray_frame

        # Break the loop if the user presses 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop the RealSense pipeline
    pipeline.stop()
    cv2.destroyAllWindows()