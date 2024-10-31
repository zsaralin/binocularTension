import sys
import pyrealsense2 as rs
import numpy as np
import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from movement_detection.pose_detection import Detector
from rgb_drawing_utils import draw_keypoints_manually, draw_skeleton, draw_movement_boxes, draw_person_bounding_boxes
from detection_data import DetectionData  # Import the shared data class

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

        # Set up the QLabel to display the video feed
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setScaledContents(True)  # Allow QLabel to scale content

        # Create a layout and add the QLabel
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Initialize the detector
        self.detector = Detector()

        # Set up a QTimer to call the update_frame method regularly
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 30 ms ~ 33 FPS

    def update_frame(self):
        # Get the frames from the shared RealSense manager
        color_frame = self.rs_manager.get_color_frame()

        if not color_frame:
            return

        # Convert RealSense frame to NumPy array
        color_image = np.asanyarray(color_frame.get_data())

        # Make a copy of the image to draw keypoints and skeleton on
        display_image = color_image.copy()

        # Run detection (movement and pose) using the detector
        tracks, keypoints_data, detections, person_boxes, person_moving_status, non_person_movement_boxes, persons_with_ids = \
            self.detector.detect_movement_and_pose(display_image)

        # Update shared detection data with the new results
        self.detection_data.set_person_moving_status(person_moving_status)
        self.detection_data.set_non_person_movement_boxes(non_person_movement_boxes)
        self.detection_data.set_persons_with_ids(persons_with_ids)

        # Draw keypoints and skeletons on the copied image
        draw_keypoints_manually(display_image, keypoints_data)
        draw_skeleton(display_image, keypoints_data)

        active_movement_id = self.detection_data.get_active_movement_id()
        active_movement_type = self.detection_data.get_active_movement_type()

        # Draw bounding boxes for persons and movement
        draw_person_bounding_boxes(tracks, display_image, person_moving_status, active_movement_id, active_movement_type, self.detection_data)
        draw_movement_boxes(non_person_movement_boxes, display_image, active_movement_id, active_movement_type,  self.detection_data)

        # Flip the image for a mirroring effect
        display_image = cv2.flip(display_image, 1)

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
