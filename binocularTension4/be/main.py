import sys
import math
import numpy as np
import pyrealsense2 as rs
from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QLabel, QDesktopWidget, QSizePolicy, QPushButton, QGroupBox, QVBoxLayout, QWidget, QHBoxLayout, QSpacerItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QSurfaceFormat
from pointcloud import GLWidget  # Assuming you have this in 'pointcloud.py'
from control_panel import ControlPanelWidget  # Assuming you have this in 'control_panel.py'
from rgbcam import RGBWidget
from realsense import RealSenseManager
from pointcloud_legend import PCLegendWidget  # Legend for point cloud
from rgb_legend import RGBLegendWidget        # Legend for RGB camera
from eye_widget import EyeWidget
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        # Define aspect ratios for each widget
        self.control_panel_ratio = 1 / 1   # Control panel square aspect ratio
        self.rgb_ratio = 848 / 480         # RGB widget aspect ratio
        self.pointcloud_ratio = 848 / 480  # Point cloud widget aspect ratio

        # Create an instance of the RealSenseManager to share between widgets
        self.rs_manager = RealSenseManager()

        # Create the splitter
        splitter = QSplitter(Qt.Horizontal)  # Horizontal splitter for side-by-side layout

        # Create the layout for the point cloud (with bottom margin)
        self.pointcloud_layout = QVBoxLayout()
        self.pointcloud = GLWidget(self.rs_manager, self)
        self.pointcloud.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create the ControlPanelWidget for the control panel with minimal width
        self.control_panel = ControlPanelWidget(self )
        self.control_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # Add point cloud to layout and set bottom margin
        self.pointcloud_layout.addWidget(self.pointcloud)
        self.pointcloud_layout.setContentsMargins(0, 0, 0, 10)  # Small bottom margin

        # Wrap the point cloud layout in a container widget
        self.pointcloud_container = QWidget()
        self.pointcloud_container.setLayout(self.pointcloud_layout)

        # Create layout for RGB camera (with bottom margin)
        self.rgb_layout = QVBoxLayout()
        self.rgb_cam = RGBWidget(self.rs_manager, self)
        self.rgb_cam.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add RGB camera to layout and set bottom margin
        self.rgb_layout.addWidget(self.rgb_cam)
        self.rgb_layout.setContentsMargins(0, 0, 0, 10)  # Small bottom margin

        # Wrap the RGB layout in a container widget
        self.rgb_container = QWidget()
        self.rgb_container.setLayout(self.rgb_layout)

        # Create a new container for the legends with a QVBoxLayout and add left-aligned HBoxLayouts
        self.legend_layout = QVBoxLayout()
        
        # Left-align each legend using an HBoxLayout
        rgb_legend_container = QWidget()
        rgb_legend_layout = QHBoxLayout()
        self.rgb_legend = RGBLegendWidget(self)
        rgb_legend_layout.addWidget(self.rgb_legend)
        rgb_legend_layout.addStretch()  # Prevent stretching to the right
        rgb_legend_container.setLayout(rgb_legend_layout)

        pointcloud_legend_container = QWidget()
        pointcloud_legend_layout = QHBoxLayout()
        self.pointcloud_legend = PCLegendWidget(self)
        pointcloud_legend_layout.addWidget(self.pointcloud_legend)
        pointcloud_legend_layout.addStretch()  # Prevent stretching to the right
        pointcloud_legend_container.setLayout(pointcloud_legend_layout)

        rgb_label = QLabel("RGB Legend")
        pointcloud_label = QLabel("PointCloud Legend")

        # Adjust label alignment if needed
        rgb_label.setAlignment(Qt.AlignCenter)
        pointcloud_label.setAlignment(Qt.AlignCenter)

        # Add the labels and legends to the layout in order
        self.legend_layout.addWidget(rgb_label)
        self.legend_layout.addWidget(rgb_legend_container)
        self.legend_layout.addWidget(pointcloud_label)
        self.legend_layout.addWidget(pointcloud_legend_container)
        self.eye_widget = EyeWidget(self)  # Initialize EyeWidget
        self.eye_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add EyeWidget below the legends
        self.legend_layout.addWidget(self.eye_widget)
        self.legend_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))  # Spacer between legends

        # Viewpoints section with buttons
        viewpoint_group = QGroupBox("Point Cloud Viewpoints")
        viewpoint_layout = QHBoxLayout()

        # Define viewpoint buttons
        top_button = QPushButton("Top")
        top_button.clicked.connect(self.pointcloud.set_top_view)

        left_button = QPushButton("Left")
        left_button.clicked.connect(self.pointcloud.set_left_view)

        right_button = QPushButton("Right")
        right_button.clicked.connect(self.pointcloud.set_right_view)

        front_button = QPushButton("Front")
        front_button.clicked.connect(self.pointcloud.set_front_view)

        # Add buttons to the viewpoint layout
        viewpoint_layout.addWidget(top_button)
        viewpoint_layout.addWidget(left_button)
        viewpoint_layout.addWidget(right_button)
        viewpoint_layout.addWidget(front_button)

        viewpoint_group.setLayout(viewpoint_layout)
        self.legend_layout.addWidget(viewpoint_group)
 
        # Wrap the legend layout in a container widget
        self.legend_container = QWidget()
        self.legend_container.setLayout(self.legend_layout)
        self.legend_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # Set fixed width for legend column

        # Add widgets to the splitter with specific stretch factors for width
        splitter.addWidget(self.control_panel)
        splitter.addWidget(self.rgb_container)
        splitter.addWidget(self.pointcloud_container)
        splitter.addWidget(self.legend_container)  # Add the legend container as a new column

        splitter.setStretchFactor(0, 1)  # Control panel (15% width)
        splitter.setStretchFactor(1, 3)  # RGB (42.5% width)
        splitter.setStretchFactor(2, 3)  # Point cloud (42.5% width)
        splitter.setStretchFactor(3, 1)  # Legends column

        # Set the splitter as the central widget
        self.setCentralWidget(splitter)

        # Set window title and a minimum initial size
        self.setWindowTitle("Point Cloud Viewer with RGB Camera, Control Panel, and Legends")
        self.setMinimumSize(1920, 600)  # Starting minimum size to fit layout well

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
        """Maintain aspect ratio of widgets on window resize, maximizing widget size based on available space."""
        # Get current window dimensions
        total_width = self.width()
        total_height = self.height()

        # Dedicate 20% of the width to the control panel and legends combined
        control_panel_width = int(total_width * 0.2)
        legend_width = int(total_width * 0.1)
        remaining_width = total_width - control_panel_width - legend_width
        remaining_height = total_height

        # Calculate the maximum dimensions for RGB based on aspect ratio
        rgb_width = min(int(remaining_width / 2), int(remaining_height * self.rgb_ratio))
        rgb_height = int(rgb_width / self.rgb_ratio)

        # Set dimensions for point cloud based on the same scaling factor for consistency
        pointcloud_width = rgb_width
        pointcloud_height = rgb_height

        # Apply calculated sizes to widgets
        self.control_panel.setFixedWidth(control_panel_width)
        self.legend_container.setFixedWidth(legend_width)
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
