import cv2
import numpy as np
import pyrealsense2 as rs

# Configure depth stream
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, rs.format.z16, 30)

# Start streaming
pipeline.start(config)

# Get stream profile and intrinsics
profile = pipeline.get_active_profile()
depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
intrinsics = depth_profile.get_intrinsics()
w, h = intrinsics.width, intrinsics.height

# Processing blocks
pc = rs.pointcloud()
out = np.zeros((h, w), dtype=np.uint8)

while True:
    # Wait for frames
    frames = pipeline.wait_for_frames()
    depth_frame = frames.get_depth_frame()

    # Skip if no frame
    if not depth_frame:
        continue

    # Process point cloud
    points = pc.calculate(depth_frame)
    v = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)  # xyz

    # Filter valid points (non-zero z-values)
    valid = v[:, 2] > 0
    v = v[valid]

    # Project 3D points to 2D screen coordinates
    proj = v[:, :2] / v[:, 2:3] * (w, h) + (w / 2, h / 2)
    proj = proj.astype(np.int32)

    # Clip points within screen bounds
    mask = (proj[:, 0] >= 0) & (proj[:, 0] < w) & (proj[:, 1] >= 0) & (proj[:, 1] < h)
    proj = proj[mask]
    z_values = v[mask, 2]

    # Map depth (z-values) to grayscale (0-255)
    z_min, z_max = z_values.min(), z_values.max()
    intensity = 255 * (1 - (z_values - z_min) / (z_max - z_min))  # Inverse mapping for visual clarity
    intensity = intensity.astype(np.uint8)

    # Render the point cloud with depth-based grayscale shading
    out.fill(0)
    out[proj[:, 1], proj[:, 0]] = intensity

    # Display the result
    cv2.imshow("Point Cloud", out)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Stop streaming
pipeline.stop()
cv2.destroyAllWindows()
