import sys
import math
import numpy as np
import pyrealsense2 as rs
from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QDesktopWidget, QSizePolicy, QVBoxLayout, QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QSurfaceFormat, QColor, QPalette
from OpenGL.GL import *
from OpenGL.GLU import *
from pointcloud import GLWidget  # Assuming you have this in 'pointcloud.py'
from control_panel import ControlPanelWidget  # Assuming you have this in 'control_panel.py'
from rgbcam import RGBWidget
from realsense import RealSenseManager
from pointcloud_legend import PCLegendWidget  # Point cloud-specific legend
from rgb_legend import RGBLegendWidget        # RGB camera-specific legend

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Define aspect ratios for each widget
        self.control_panel_ratio = 1 / 1   # Control panel square aspect ratio
        self.rgb_ratio = 640 / 480         # RGB widget aspect ratio
        self.pointcloud_ratio = 640 / 480  # Point cloud widget aspect ratio

        # Create an instance of the RealSenseManager to share between widgets
        self.rs_manager = RealSenseManager()

        # Create the splitter
        splitter = QSplitter(Qt.Horizontal)  # Horizontal splitter for side-by-side layout

        # Create the ControlPanelWidget for the control panel
        self.control_panel = ControlPanelWidget(self)
        self.control_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create the layout for point cloud and its legend
        self.pointcloud_layout = QVBoxLayout()
        self.pointcloud = GLWidget(self.rs_manager, self)
        self.pointcloud.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pointcloud_legend = PCLegendWidget(self)  # Create point cloud legend

        # Add point cloud and its legend to layout
        self.pointcloud_layout.addWidget(self.pointcloud)
        self.pointcloud_layout.addWidget(self.pointcloud_legend)

        # Wrap the point cloud layout in a container widget
        self.pointcloud_container = QWidget()
        self.pointcloud_container.setLayout(self.pointcloud_layout)

        # Create layout for RGB camera and its legend
        self.rgb_layout = QVBoxLayout()
        self.rgb_cam = RGBWidget(self.rs_manager, self)
        self.rgb_cam.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.rgb_legend = RGBLegendWidget(self)  # Create RGB camera legend

        # Add RGB camera and its legend to layout
        self.rgb_layout.addWidget(self.rgb_cam)
        self.rgb_layout.addWidget(self.rgb_legend)

        # Wrap the RGB layout in a container widget
        self.rgb_container = QWidget()
        self.rgb_container.setLayout(self.rgb_layout)

        # Add widgets to the splitter
        splitter.addWidget(self.control_panel)
        splitter.addWidget(self.rgb_container)
        splitter.addWidget(self.pointcloud_container)

        # Set the splitter as the central widget
        self.setCentralWidget(splitter)

        # Set window title and a minimum initial size
        self.setWindowTitle("Point Cloud Viewer with RGB Camera and Control Panel")
        self.setMinimumSize(1800, 700)  # Starting minimum size to fit layout well

        # Center the window on the screen
        self.center_window()
        self.show()

    def center_window(self):
        """Center the main window on the screen."""
        screen = QDesktopWidget().screenGeometry()
        window = self.geometry()
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        self.move(x, y)

    def resizeEvent(self, event):
        """Maintain aspect ratio of widgets on window resize."""
        # Get current window dimensions
        total_width = self.width()
        total_height = self.height()

        # Calculate available width for RGB and Point Cloud widgets
        remaining_width = total_width * 0.8
        rgb_width = int(remaining_width * 0.5)
        rgb_height = int(rgb_width / self.rgb_ratio)
        pointcloud_width = rgb_width
        pointcloud_height = int(pointcloud_width / self.pointcloud_ratio)

        # Adjust size policies to allow expansion
        self.control_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.rgb_cam.setFixedSize(rgb_width, rgb_height)
        self.pointcloud.setFixedSize(pointcloud_width, pointcloud_height)

        super(MainWindow, self).resizeEvent(event)

    def closeEvent(self, event):
        # Stop the RealSense pipeline when closing the window
        self.rs_manager.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set OpenGL format (optional)
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)

    window = MainWindow()
    sys.exit(app.exec_())
