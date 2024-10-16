import cv2
import numpy as np
import time

# Initialize previous blob positions and human blob tracker
prev_blob_positions = []
prev_blob_areas = []  # Track previous blob areas for area-based movement detection
human_blobs = []
blob_depths = []

# Set a minimum blob area threshold
MIN_BLOB_AREA = 200  # Adjust this value based on your needs

# Variable to store the last time coordinates were returned
last_return_time = 0  # Initialize last return time to 0

def render_2d(out, verts, transform_gui=None, nose_keypoint=None):
    global last_return_time
    fixed_scale = 200.0
    if transform_gui is not None:
        movement_threshold = transform_gui.get_movement_threshold()
    else:
        movement_threshold = 20.0

    global prev_blob_positions, prev_blob_areas, human_blobs, blob_depths
    out.fill(0)

    # Guard clause to exit if verts is None or empty
    if verts is None or len(verts) == 0:
        print("No vertices provided.")
        return None

    # Project to 2D and scale
    center_x, center_y = out.shape[1] // 2, out.shape[0] // 2
    verts_2d = verts[:, :2] * fixed_scale
    verts_2d[:, 0] += center_x
    verts_2d[:, 1] += center_y

    # Get the depth (z-coordinates)
    depths = verts[:, 2]

    # Guard clause to exit if depths are None or empty
    if depths is None or len(depths) == 0:
        print("No depth data available.")
        return None

    # Create a mask for valid points
    valid_points = (verts_2d[:, 0] >= 0) & (verts_2d[:, 0] < out.shape[1]) & \
                   (verts_2d[:, 1] >= 0) & (verts_2d[:, 1] < out.shape[0])

    # Guard clause if no valid points exist after applying the mask
    if not np.any(valid_points):
        print("No valid points within frame.")
        return None

    # Get valid coordinates and depths
    valid_x = verts_2d[valid_points][:, 0].astype(int)
    valid_y = verts_2d[valid_points][:, 1].astype(int)
    valid_depths = depths[valid_points]

    # Guard clause if no valid coordinates or depths
    if len(valid_x) == 0 or len(valid_y) == 0 or len(valid_depths) == 0:
        print("No valid coordinates or depth values available.")
        return None

    # Create a blank binary mask (to hold blobs)
    binary_mask = np.zeros(out.shape[:2], dtype=np.uint8)

    # Directly set binary mask points as 'blobs'
    for x, y in zip(valid_x, valid_y):
        binary_mask[y, x] = 255

    # Apply morphological operations to clean up the mask (if needed)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)

    # Find contours (blobs)
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Guard clause if no contours are found
    if not contours:
        print("No blobs detected.")
        return None

    # Get current blob centroids, areas, and depths
    current_blob_centroids = []
    current_blob_areas = []
    current_blob_depths = []
    valid_contours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < MIN_BLOB_AREA:
            continue
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            current_blob_centroids.append((cX, cY))
            current_blob_areas.append(area)
            mask = np.zeros_like(binary_mask)
            cv2.drawContours(mask, [contour], -1, 255, -1)
            blob_depth = np.mean(valid_depths[mask[valid_y, valid_x] == 255])
            current_blob_depths.append(blob_depth)
            valid_contours.append(contour)

    # Guard clause if no valid blobs are found
    if not current_blob_centroids or not current_blob_depths:
        print("No valid blobs found.")
        return None

    # Initialize movement_detected and is_human lists
    movement_detected = [False] * len(current_blob_centroids)
    is_human_blob = [False] * len(current_blob_centroids)

    # Track movement between frames
    for i, (cur_cx, cur_cy) in enumerate(current_blob_centroids):
        for j, (prev_cx, prev_cy) in enumerate(prev_blob_positions):
            distance = np.hypot(cur_cx - prev_cx, cur_cy - prev_cy)
            area_change = abs(current_blob_areas[i] - prev_blob_areas[j])
            if distance > movement_threshold and area_change > 50:
                movement_detected[i] = True

    # Update previous blob positions and areas for tracking
    prev_blob_positions = current_blob_centroids
    prev_blob_areas = current_blob_areas
    human_blobs = is_human_blob
    blob_depths = current_blob_depths

    # Find the closest moving blob
    closest_blob_index = None
    moving_blob_indices = [i for i, moved in enumerate(movement_detected) if moved]
    if moving_blob_indices:
        closest_blob_index = min(moving_blob_indices, key=lambda i: current_blob_depths[i])
    #
    if not contours:
        print("No blobs detected.")
        return None
    # # Draw filled contours
    for i, contour in enumerate(valid_contours):
        if i < len(movement_detected):  # Ensure we're within bounds
            color = (0, 0, 255) if movement_detected[i] and i == closest_blob_index else (255, 255, 255)
            cv2.drawContours(out, [contour], -1, color, -1)

    # Return the closest moving blob's position and depth, if conditions are met
    current_time = time.time()
    if closest_blob_index is not None:
        last_return_time = current_time
        coords = current_blob_centroids[closest_blob_index]
        depth = current_blob_depths[closest_blob_index]
        combined_coords = (coords[0], coords[1], depth)
        print(combined_coords)
        return combined_coords

    return None