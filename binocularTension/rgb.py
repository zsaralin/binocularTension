# rgb.py

import pyrealsense2 as rs
import cv2
import numpy as np

def initialize_rgb_pipeline():
    pipeline = rs.pipeline()
    config = rs.config()

    # Enable color stream
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    # Start pipeline
    pipeline.start(config)

    return pipeline

def process_rgb_frame(pipeline):
    frames = pipeline.wait_for_frames()
    color_frame = frames.get_color_frame()

    # Convert the image to a numpy array and flip it horizontally (if needed)
    color_image = np.asanyarray(color_frame.get_data())
    color_image = cv2.flip(color_image, 1)  # Flip horizontally

    return color_image
