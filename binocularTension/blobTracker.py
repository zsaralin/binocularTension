import cv2
import numpy as np

class BlobTracker:
    def __init__(self, movement_threshold=10, area_change_threshold=0.1):
        self.prev_center = None
        self.prev_area = None
        self.movement_threshold = movement_threshold
        self.area_change_threshold = area_change_threshold

    def detect_motion(self, binary_mask):
        # Find contours
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return False, 0, 0

        # Get the largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Calculate moments of the largest contour
        M = cv2.moments(largest_contour)

        if M["m00"] == 0:
            return False, 0, 0

        # Calculate center of mass
        center_x = int(M["m10"] / M["m00"])
        center_y = int(M["m01"] / M["m00"])
        current_center = (center_x, center_y)

        # Calculate area
        current_area = cv2.contourArea(largest_contour)

        if self.prev_center is None or self.prev_area is None:
            self.prev_center = current_center
            self.prev_area = current_area
            return False, 0, 0

        # Calculate movement
        movement = np.sqrt((current_center[0] - self.prev_center[0])**2 +
                           (current_center[1] - self.prev_center[1])**2)

        # Calculate area change
        area_change = abs(current_area - self.prev_area) / self.prev_area

        # Detect significant motion
        motion_detected = (movement > self.movement_threshold or
                           area_change > self.area_change_threshold)

        # Update previous values
        self.prev_center = current_center
        self.prev_area = current_area

        return motion_detected, movement, area_change

def render_2d(out, verts, transform_gui, fixed_scale=300.0, blob_smoother=None, blob_tracker=None):
    """Render the 2D representation of the 3D point cloud (front view) with motion detection."""
    if blob_smoother is None:
        blob_smoother = BlobSmoother()
    if blob_tracker is None:
        blob_tracker = BlobTracker()

    # ... [Previous render_2d code remains the same up to drawing the contour] ...

    # Draw filled contour
    cv2.drawContours(out, [smoothed_hull.astype(np.int32)], -1, (255, 255, 255), -1)

    # Create a binary mask for motion detection
    binary_mask = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)

    # Detect motion
    motion_detected, movement, area_change = blob_tracker.detect_motion(binary_mask)

    # Visualize motion detection results
    if motion_detected:
        cv2.putText(out, f"Motion Detected!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(out, f"Movement: {movement:.2f}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(out, f"Area Change: {area_change:.2%}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Apply edge smoothing
    out = cv2.GaussianBlur(out, (9, 9), 0)

    return out, motion_detected, movement, area_change

# Usage in main loop:
blob_smoother = BlobSmoother(history_length=5)
blob_tracker = BlobTracker(movement_threshold=10, area_change_threshold=0.1)

# In your main loop:
out, motion_detected, movement, area_change = render_2d(out, verts, transform_gui,
                                                        fixed_scale=300.0,
                                                        blob_smoother=blob_smoother,
                                                        blob_tracker=blob_tracker)

if motion_detected:
    print(f"Motion detected! Movement: {movement:.2f}, Area change: {area_change:.2%}")