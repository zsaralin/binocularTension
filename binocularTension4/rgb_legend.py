from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QWidget, QHBoxLayout

class RGBLegendWidget(QWidget):
    """A widget to display the point cloud legend below the GLWidget."""

    def __init__(self, parent=None):
        super(RGBLegendWidget, self).__init__(parent)
        layout = QVBoxLayout()

        # Legend items
        self.add_legend_item(layout, "Active & Moving Person", QColor(0, 255, 0))         # Green
        self.add_legend_item(layout, "Active & Stationary Person", QColor(255, 0, 255))   # Magenta
        self.add_legend_item(layout, "Non-Active & Stationary Person", QColor(255, 255, 0))  # Yellow
        self.add_legend_item(layout, "Active Moving Object", QColor(0, 180, 0))           # Dark Green
        self.add_legend_item(layout, "Non-Active Moving Object/Person", QColor(255, 0, 0))       # Red
        # Set layout and spacing
        self.setLayout(layout)
        self.setMinimumHeight(80)  # Prevent squishing when resizing

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
