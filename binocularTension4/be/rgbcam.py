import sys
import pyrealsense2 as rs
import numpy as np
import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from movement_detection.pose_detection import Detector
from rgb_drawing_utils import draw_peaks, draw_bounding_boxes
from detection_data import DetectionData  # Import the shared data class
from movement_detection.object_detection import ObjectDetector
import pyrealsense2 as rs

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
import numpy as np
import cv2

class RGBWidget(QWidget):
    def __init__(self, rs_manager, parent=None):
        super(RGBWidget, self).__init__(parent)

        self.rs_manager = rs_manager
        self.detection_data = DetectionData()

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setScaledContents(True) 

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.detector = Detector()
        self.object_detector = ObjectDetector()

        # Set up a QTimer to call the update_frame method regularly
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 30 ms ~ 33 FPS

    def update_frame(self):
        color_frame = self.rs_manager.get_color_frame()

        if color_frame is None:
            return

        # Convert RealSense frame to NumPy array
        color_image = np.asanyarray(color_frame.get_data())
        if color_image.ndim == 2:  # Single-channel grayscale
                color_image = np.stack((color_image,) * 3, axis=-1)  # Replicate grayscale data across 3 channels
            
        # Make a copy of the image to draw keypoints and skeleton on
        display_image = color_image.copy()
        display_image = cv2.flip(display_image, 1)

        depth_frame = self.rs_manager.get_depth_frame()
        intrinsics = self.rs_manager.get_depth_intrinsics()  # Get RealSense intrinsics for depth calculations
        depth_image = np.asanyarray(depth_frame.get_data())
        depth_scale = self.rs_manager.get_depth_scale()  # Scale for converting depth value to meters
        tracked_objects =self.object_detector.detect_objects(display_image,depth_image, intrinsics, depth_scale)
        draw_bounding_boxes(tracked_objects, display_image, self.detection_data.active_movement_id, self.detection_data)
        draw_peaks(tracked_objects, display_image, self.detection_data.active_movement_id, self.detection_data)

        self.detection_data.set_object_boxes(tracked_objects)
       
        # Convert to QImage to display in QLabel
        height, width, channel = display_image.shape
        bytes_per_line = 3 * width
        q_image = QImage(display_image.data, width, height, bytes_per_line, QImage.Format_BGR888)

        # Resize QPixmap to fit QLabel without cropping, while maintaining the aspect ratio
        self.label.setPixmap(QPixmap.fromImage(q_image).scaled(
            self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def resizeEvent(self, event):
        """Handle resizing of the widget to maintain the aspect ratio in QLabel."""
        if self.label.pixmap():
            # Scale the pixmap to the new QLabel size, maintaining the aspect ratio
            self.label.setPixmap(self.label.pixmap().scaled(
                self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        super(RGBWidget, self).resizeEvent(event)

    def closeEvent(self, event):
        # Clean up if needed
        event.accept()
