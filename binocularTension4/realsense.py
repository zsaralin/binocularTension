import pyrealsense2 as rs

from PyQt5.QtCore import QTimer
import pyrealsense2 as rs
import numpy as np

class RealSenseManager:
    def __init__(self):
        self.pipeline = rs.pipeline()
        config = rs.config()

        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 60)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 60)

        self.pipeline_profile = self.pipeline.start(config)

        self.color_frame = None
        self.depth_frame = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)  # Approximately 30 FPS

    def update_frames(self):
        try:
            frames = self.pipeline.wait_for_frames()
            self.color_frame = frames.get_color_frame()
            self.depth_frame = frames.get_depth_frame()
        except RuntimeError:
            print("Frame didn't arrive within 5000 ms")

    def get_color_frame(self):
        return self.color_frame

    def get_depth_frame(self):
        return self.depth_frame

    def get_depth_intrinsics(self):
        """Retrieve depth intrinsics (necessary for 2D to 3D projection)."""
        depth_stream = self.pipeline_profile.get_stream(rs.stream.depth)  # Fetch depth stream profile
        intrinsics = depth_stream.as_video_stream_profile().get_intrinsics()
        return intrinsics

    def get_depth_scale(self):
        """Retrieve the depth scale for converting depth values to meters."""
        depth_sensor = self.pipeline_profile.get_device().first_depth_sensor()
        return depth_sensor.get_depth_scale()

    def stop(self):
        self.pipeline.stop()
