from pointcloud import GLWidget  # Assuming you have this in 'pointcloud.py'
from PyQt5.QtGui import QSurfaceFormat, QColor, QPalette
from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QDesktopWidget, QSizePolicy, QVBoxLayout, QLabel, QWidget, QHBoxLayout

class PCLegendWidget(QWidget):
    """A widget to display the point cloud legend below the GLWidget."""

    def __init__(self, parent=None):
        super(PCLegendWidget, self).__init__(parent)
        layout = QVBoxLayout()

        # Legend items
        self.add_legend_item(layout, "Active Person Movement", QColor(0, 255, 0))  # Green
        self.add_legend_item(layout, "Active Object Movement", QColor(0, 180, 0))  # Dark Green
        self.add_legend_item(layout, "Other Movement/Tracked Person", QColor(255, 0, 0))  # Red

        # Set layout and spacing
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setLayout(layout)
    def add_legend_item(self, layout, text, color):
        """Helper function to create a color legend item."""
        item_layout = QHBoxLayout()
        color_label = QLabel()
        color_label.setFixedSize(10, 10)
        color_palette = color_label.palette()
        color_palette.setColor(QPalette.Window, color)
        color_label.setAutoFillBackground(True)
        color_label.setPalette(color_palette)

        label = QLabel(text)
        item_layout.addWidget(color_label)
        item_layout.addWidget(label)
        layout.addLayout(item_layout)
