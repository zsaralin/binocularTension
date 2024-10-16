# Importing Dependencies:
import cv2
import pyrealsense2 as rs
import tensorflow_hub as hub
import tensorflow as tf
import numpy as np

# Loading The Model:
model = hub.load('https://tfhub.dev/google/movenet/multipose/lightning/1')
movenet = model.signatures['serving_default']

# Optimize for GPU usage (if available):
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)

# Helper Functions:
# Drawing The Keypoints:
def draw_keypoints(frame, keypoints, confidence_threshold):
    y, x, c = frame.shape
    shaped = np.squeeze(np.multiply(keypoints, [y, x, 1]))

    for kp in shaped:
        ky, kx, kp_conf = kp
        if kp_conf > confidence_threshold:
            cv2.circle(frame, (int(kx), int(ky)), 5, (0, 255, 0), -1)

# Drawing The Edges:
edges = {
    (0, 1): 'm',
    (0, 2): 'c',
    (1, 3): 'm',
    (2, 4): 'c',
    (0, 5): 'm',
    (0, 6): 'c',
    (5, 7): 'm',
    (7, 9): 'm',
    (6, 8): 'c',
    (8, 10): 'c',
    (5, 6): 'y',
    (5, 11): 'm',
    (6, 12): 'c',
    (11, 12): 'y',
    (11, 13): 'm',
    (13, 15): 'm',
    (12, 14): 'c',
    (14, 16): 'c'
}

def draw_connections(frame, keypoints, edges, confidence_threshold):
    y, x, c = frame.shape
    shaped = np.squeeze(np.multiply(keypoints, [y, x, 1]))

    for edge, color in edges.items():
        p1, p2 = edge
        y1, x1, c1 = shaped[p1]
        y2, x2, c2 = shaped[p2]

        if (c1 > confidence_threshold) & (c2 > confidence_threshold):
            cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 4)

# Function to loop through each person detected and render:
def loop_through_people(frame, keypoints_with_scores, edges, confidence_threshold):
    for person in keypoints_with_scores:
        draw_connections(frame, person, edges, confidence_threshold)
        draw_keypoints(frame, person, confidence_threshold)

# RealSense setup:
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
pipeline.start(config)

# Frame skipping mechanism:
frame_skip = 1  # Process every second frame (change as necessary)
frame_count = 0

try:
    while True:
        # Wait for a coherent pair of frames: color and depth
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()

        if not color_frame:
            continue

        # Convert RealSense image to numpy array
        img = np.asanyarray(color_frame.get_data())

        if frame_count % frame_skip == 0:
            # resizing the image to a smaller resolution for faster inference:
            image = tf.cast(tf.image.resize_with_pad(tf.expand_dims(img, axis=0), 192, 256), dtype=tf.int32)

            # detection:
            results = movenet(image)
            keypoints = results['output_0'].numpy()[:, :, :51].reshape((6, 17, 3))

            # Render keypoints
            loop_through_people(img, keypoints, edges, 0.1)

        # Show the image with keypoints (update every frame)
        cv2.imshow('MoveNet Multipose - RealSense', img)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

        frame_count += 1  # Increment frame counter

finally:
    # Stop streaming
    pipeline.stop()
    cv2.destroyAllWindows()
