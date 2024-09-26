import cv2
import numpy as np
from scipy.ndimage import gaussian_filter

# Track previous blob positions and sizes
previous_blobs = []

def render_2d(image, vertices, contour_canvas, depth_image, project, min_blob_size=1000, smooth_factor=0.9, stability_frames=3):
    global previous_blobs

    # Project the vertices to 2D
    proj = project(vertices)
    j, i = proj.astype(np.int32).T

    # Create a mask to select valid points inside the image boundaries
    h, w = image.shape[:2]
    valid = (i >= 0) & (i < h) & (j >= 0) & (j < w)

    if not np.any(valid):
        return

    i, j = i[valid], j[valid]
    z_values = vertices[valid, 2]

    if z_values.size == 0:
        return

    # Create a blank mask for the blobs
    mask = np.zeros((h, w), dtype=np.uint8)

    # Draw all valid points on the mask
    mask[i, j] = 255

    # Apply Gaussian filter to smooth the mask and remove jittery pixels
    mask = gaussian_filter(mask, sigma=5)  # Increased sigma for stronger smoothing

    # Threshold the mask to create a binary image after smoothing
    _, mask = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)

    # Erode the mask to reduce unstable edges
    kernel = np.ones((15, 15), np.uint8)  # Smaller kernel for erosion
    mask = cv2.erode(mask, kernel, iterations=2)

    # Apply morphological closing to clean up the mask further
    kernel = np.ones((20, 20), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Find contours (blobs)
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Process and draw valid contours
    valid_contours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_blob_size:
            x, y, w, h = cv2.boundingRect(contour)
            center = (x + w // 2, y + h // 2)

            # Smooth the center position with previous positions if available
            if previous_blobs:
                prev_center = min(previous_blobs, key=lambda b: np.linalg.norm(np.array(b[0]) - np.array(center)))[0]
                center = tuple(map(int, smooth_factor * np.array(prev_center) + (1 - smooth_factor) * np.array(center)))

            # Color based on depth
            depth = np.mean(z_values[(i >= y) & (i < y+h) & (j >= x) & (j < x+w)])
            color = cv2.applyColorMap(np.array([int(depth * 255)], dtype=np.uint8), cv2.COLORMAP_JET)[0][0]

            # Draw the contour
            cv2.drawContours(contour_canvas, [contour], -1, color.tolist(), thickness=cv2.FILLED)

            # Draw the center point
            cv2.circle(contour_canvas, center, 5, (0, 255, 0), -1)

            # Track the center and size of the blob for future stabilization
            valid_contours.append((center, color.tolist()))

    # Update previous_blobs for the next frame
    previous_blobs = valid_contours

    return contour_canvas
