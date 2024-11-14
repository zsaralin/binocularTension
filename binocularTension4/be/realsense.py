import pyrealsense2 as rs
from PyQt5.QtCore import QTimer
import numpy as np
import cv2
from detection_data import DetectionData
class RealSenseManager:
    def __init__(self):
        self.pipeline = rs.pipeline()
        config = rs.config()

        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 60)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 60)
        config.enable_stream(rs.stream.infrared, 1, 640, 480, rs.format.y8, 60)

        self.pipeline_profile = self.pipeline.start(config)

        self.color_frame = None
        self.depth_frame = None
        self.infrared_frame = None
        self.brightness_threshold = 100  # Brightness threshold for switching to infrared

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)  # Approximately 30 FPS

        self.detection_data = DetectionData()

    def update_frames(self):
        try:
            frames = self.pipeline.wait_for_frames()
            self.color_frame = frames.get_color_frame()
            self.depth_frame = frames.get_depth_frame()
            self.infrared_frame = frames.get_infrared_frame()

            # Check brightness of color frame
            if self.color_frame:
                # Convert color frame to numpy array to calculate brightness
                color_image = np.asanyarray(self.color_frame.get_data())
                brightness = np.mean(cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY))

                # Use infrared frame as color if brightness is below threshold
                if brightness < self.brightness_threshold:
                    self.detection_data.set_is_dark(True)
                    self.color_frame = self.infrared_frame
                else:
                    self.detection_data.set_is_dark(False)


        except RuntimeError:
            print("Frame didn't arrive within 5000 ms")

    def get_color_frame(self):
        return self.color_frame  # Returns either color or infrared frame as a pyrealsense2 frame

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
