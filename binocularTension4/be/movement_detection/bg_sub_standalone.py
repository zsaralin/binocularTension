import cv2
import numpy as np
import pyrealsense2 as rs

def main():
    # Configure RealSense pipeline
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    pipeline.start(config)

    # Create background subtractor
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=25, detectShadows=False)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    try:
        while True:
            # Wait for a coherent pair of frames
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            if not color_frame:
                continue

            # Convert images to numpy arrays
            color_image = np.asanyarray(color_frame.get_data())

            # Apply background subtraction
            fg_mask = bg_subtractor.apply(color_image)

            # Morphological operations to reduce noise
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)

            # Find contours in the foreground mask
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Draw bounding boxes around detected contours on the original image
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # filter out small contours
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(color_image, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # Display both images side by side
            # Convert fg_mask to BGR for side-by-side stacking
            fg_bgr = cv2.cvtColor(fg_mask, cv2.COLOR_GRAY2BGR)
            combined = np.hstack((color_image, fg_bgr))

            cv2.imshow('RealSense RGB (Left) | Foreground Mask (Right)', combined)

            # Press 'q' to exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Stop the pipeline
        pipeline.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
