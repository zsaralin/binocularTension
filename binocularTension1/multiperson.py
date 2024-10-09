import cv2
import pyrealsense2 as rs
import numpy as np
from ultralytics import YOLO
from collections import deque

# Load the YOLOv8 model with verbose=False to suppress output
model = YOLO("yolov8n.pt")
model.verbose = False

# Configure RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()

# Enable RGB and depth streams
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# Start the RealSense pipeline
profile = pipeline.start(config)

# Get the depth scale
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()

# Initialize variables for motion detection
previous_frame = None
motion_threshold = 30
min_area = 500

# Dictionary to store object tracking data
tracked_objects = {}

# Moving average window size
window_size = 5

# Movement threshold (in pixels)
movement_threshold = 10

def process_frame(color_image, depth_image, depth_scale, model, tracked_objects, window_size, movement_threshold):
    global previous_frame
    moving_objects = []

    # Convert to grayscale for motion detection
    gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # If this is the first frame, initialize it and return
    if previous_frame is None:
        previous_frame = gray
        return color_image, moving_objects

    # Compute absolute difference between current and previous frame
    frame_delta = cv2.absdiff(previous_frame, gray)
    thresh = cv2.threshold(frame_delta, motion_threshold, 255, cv2.THRESH_BINARY)[1]

    # Dilate the thresholded image to fill in holes, then find contours
    thresh = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    motion_mask = np.zeros(color_image.shape[:2], dtype=np.uint8)

    for contour in contours:
        if cv2.contourArea(contour) > min_area:
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(motion_mask, (x, y), (x + w, y + h), 255, -1)

    # Run YOLOv8 tracking on the frame, persisting tracks between frames
    results = model.track(color_image, persist=True, verbose=False)

    # Filter results based on motion mask
    if results[0].boxes is not None and len(results[0].boxes) > 0:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        ids = results[0].boxes.id.cpu().numpy() if results[0].boxes.id is not None else None

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box[:4])
            if np.any(motion_mask[y1:y2, x1:x2] > 0):
                object_id = int(ids[i]) if ids is not None else i
                midpoint = ((x1 + x2) // 2, (y1 + y2) // 2)
                width = x2 - x1
                height = y2 - y1

                # Get depth at midpoint, ensuring it's within the image bounds
                depth_y = min(max(midpoint[1], 0), depth_image.shape[0] - 1)
                depth_x = min(max(midpoint[0], 0), depth_image.shape[1] - 1)
                depth = depth_image[depth_y, depth_x] * depth_scale

                if object_id not in tracked_objects:
                    tracked_objects[object_id] = {
                        'midpoints': deque(maxlen=window_size),
                        'widths': deque(maxlen=window_size),
                        'heights': deque(maxlen=window_size),
                        'depths': deque(maxlen=window_size)
                    }

                tracked_objects[object_id]['midpoints'].append(midpoint)
                tracked_objects[object_id]['widths'].append(width)
                tracked_objects[object_id]['heights'].append(height)
                tracked_objects[object_id]['depths'].append(depth)

                avg_midpoint = np.mean(tracked_objects[object_id]['midpoints'], axis=0)
                avg_width = np.mean(tracked_objects[object_id]['widths'])
                avg_height = np.mean(tracked_objects[object_id]['heights'])
                avg_depth = np.mean(tracked_objects[object_id]['depths'])

                # Check if the object has moved significantly
                if len(tracked_objects[object_id]['midpoints']) > 1:
                    prev_midpoint = tracked_objects[object_id]['midpoints'][-2]
                    movement = np.linalg.norm(np.array(midpoint) - np.array(prev_midpoint))
                    if movement > movement_threshold:
                        print(f"Object {object_id} moved: Midpoint (x, y, z) = ({avg_midpoint[0]:.2f}, {avg_midpoint[1]:.2f}, {avg_depth:.3f}m)")
                        moving_objects.append({
                            'id': object_id,
                            'midpoint': (avg_midpoint[0], avg_midpoint[1], avg_depth),
                            'bbox': (x1, y1, x2, y2)
                        })

                # Draw bounding box and midpoint
                cv2.rectangle(color_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.circle(color_image, (int(avg_midpoint[0]), int(avg_midpoint[1])), 4, (0, 0, 255), -1)

    # Update previous frame
    previous_frame = gray

    return color_image, moving_objects

def get_processed_frame(pipeline, model, tracked_objects, window_size, movement_threshold):
    frames = pipeline.wait_for_frames()
    color_frame = frames.get_color_frame()
    depth_frame = frames.get_depth_frame()

    if not color_frame or not depth_frame:
        return None

    color_image = np.asanyarray(color_frame.get_data())
    depth_image = np.asanyarray(depth_frame.get_data())

    return process_frame(color_image, depth_image, depth_scale, model, tracked_objects, window_size, movement_threshold)

if __name__ == "__main__":
    try:
        while True:
            processed_frame = get_processed_frame(pipeline, model, tracked_objects, window_size, movement_threshold)
            
            if processed_frame is not None:
                cv2.imshow("YOLOv8 Tracking - RealSense (Moving Objects)", processed_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        pipeline.stop()
        cv2.destroyAllWindows()