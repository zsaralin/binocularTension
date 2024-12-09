import cv2
import pyrealsense2 as rs
import numpy as np

# Configure the RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.infrared, 848, 480, rs.format.y8, 30)  # Enable infrared stream
pipeline.start(config)

# Initialize background subtractor
back_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=120, detectShadows=False)

# Function to apply morphological operations for noise reduction
def clean_mask(mask):
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    return mask

# Function to merge nearby bounding boxes
def merge_bounding_boxes(bounding_boxes, proximity_threshold=20):
    merged_boxes = []
    for box in bounding_boxes:
        x, y, w, h = box
        merged = False
        for merged_box in merged_boxes:
            mx, my, mw, mh = merged_box
            # Check if the boxes are close to each other
            if abs(x - mx) < proximity_threshold and abs(y - my) < proximity_threshold:
                # Merge the boxes
                new_x = min(x, mx)
                new_y = min(y, my)
                new_w = max(x + w, mx + mw) - new_x
                new_h = max(y + h, my + mh) - new_y
                merged_boxes[merged_boxes.index(merged_box)] = (new_x, new_y, new_w, new_h)
                merged = True
                break
        if not merged:
            merged_boxes.append((x, y, w, h))
    return merged_boxes

try:
    while True:
        # Capture frame from RealSense camera
        frames = pipeline.wait_for_frames()
        ir_frame = frames.get_infrared_frame()  # Get the infrared frame
        if not ir_frame:
            continue
        current_frame = np.asanyarray(ir_frame.get_data())  # Convert infrared frame to numpy array

        # Apply background subtraction with a learning rate
        foreground_mask = back_sub.apply(current_frame, learningRate=0.01)
        cleaned_mask = clean_mask(foreground_mask)

        # Threshold to keep only significant white areas
        _, binary_mask = cv2.threshold(cleaned_mask, 90, 255, cv2.THRESH_BINARY)

        # Find contours for detected objects
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get bounding boxes for each contour
        bounding_boxes = [cv2.boundingRect(contour) for contour in contours if cv2.contourArea(contour) > 200]

        # Merge nearby bounding boxes
        merged_boxes = merge_bounding_boxes(bounding_boxes, proximity_threshold=20)

        # Draw merged bounding boxes on the left side of the frame only
        for (x, y, w, h) in merged_boxes:
            cv2.rectangle(current_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Display the frames
        cv2.imshow('Bounding Boxes (Left Side)', current_frame)
        cv2.imshow('Foreground Mask', binary_mask)

        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Clean up
    pipeline.stop()
    cv2.destroyAllWindows()
