import cv2
import numpy as np

# Initialize previous blob positions
prev_blob_positions = []

def render_2d(out, verts, fixed_scale=200.0, movement_threshold=10.0):
    """Render the 2D representation of the 3D point cloud (front view) with movement detection."""
    global prev_blob_positions
    out.fill(0)

    # Project to 2D and scale
    center_x, center_y = out.shape[1] // 2, out.shape[0] // 2
    verts_2d = verts[:, :2] * fixed_scale
    verts_2d[:, 0] += center_x
    verts_2d[:, 1] += center_y

    # Create a mask for valid points
    valid_points = (verts_2d[:, 0] >= 0) & (verts_2d[:, 0] < out.shape[1]) & \
                   (verts_2d[:, 1] >= 0) & (verts_2d[:, 1] < out.shape[0])

    # Get valid coordinates
    valid_x = verts_2d[valid_points][:, 0].astype(int)
    valid_y = verts_2d[valid_points][:, 1].astype(int)

    # Create a heatmap
    heatmap = np.zeros(out.shape[:2], dtype=np.float32)
    for x, y in zip(valid_x, valid_y):
        cv2.circle(heatmap, (x, y), 3, 1, -1)

    heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, binary_mask = cv2.threshold(heatmap, 100, 255, cv2.THRESH_BINARY)

    # Apply morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (50, 50))
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)

    # Find contours (blobs)
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Get current blob centroids
    current_blob_centroids = []
    for contour in contours:
        M = cv2.moments(contour)
        if M["m00"] != 0:  # Avoid division by zero
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            current_blob_centroids.append((cX, cY))

    # Initialize movement_detected list
    movement_detected = [False] * len(current_blob_centroids)

    # Track movement between frames
    if prev_blob_positions:
        prev_centroids_matched = [False] * len(prev_blob_positions)
        for i, (cur_cx, cur_cy) in enumerate(current_blob_centroids):
            # Find the closest previous centroid
            min_distance = float('inf')
            min_index = -1
            for j, (prev_cx, prev_cy) in enumerate(prev_blob_positions):
                if prev_centroids_matched[j]:
                    continue  # Skip if already matched
                distance = np.hypot(cur_cx - prev_cx, cur_cy - prev_cy)
                if distance < min_distance:
                    min_distance = distance
                    min_index = j
            if min_index >= 0:
                prev_centroids_matched[min_index] = True
                if min_distance > movement_threshold:
                    movement_detected[i] = True
                    print(f"Movement detected for blob at ({cur_cx}, {cur_cy})")

    # Update previous blob positions
    prev_blob_positions = current_blob_centroids

    # Draw filled contours with color change if movement detected
    for i, contour in enumerate(contours):
        if movement_detected[i]:
            color = (0, 0, 255)  # Red for movement detected
        else:
            color = (255, 255, 255)  # White for no movement
        cv2.drawContours(out, [contour], -1, color, -1)
