from PyQt5.QtGui import QColor, QPalette, QPixmap, QPainter, QPen
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QWidget, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt

class RGBLegendWidget(QWidget):
    """A widget to visually display the line style and color legend for movement."""

    def __init__(self, parent=None):
        super(RGBLegendWidget, self).__init__(parent)
        layout = QVBoxLayout()

        # Add legend items with solid and dotted line representations
        self.add_legend_item(layout, "Active & Moving", QColor(0, 255, 0), solid=True)   # Green solid line
        self.add_legend_item(layout, "Active & Stationary", QColor(0, 255, 0), solid=False)  # Green dotted line
        self.add_legend_item(layout, "Non-Active Moving Object/Person", QColor(255, 0, 0), solid=True)  # Red solid line
        self.add_legend_item(layout, "Non-Active Stationary Person", QColor(255, 0, 0), solid=False)  # White dotted line
        self.add_legend_item(layout, "Other Moving", QColor(255, 0, 0), solid=True)  # Red solid line for other moving

        # Set layout and spacing
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setLayout(layout)

    def add_legend_item(self, layout, text, color, solid=True):
        """Helper function to create a color legend item with a line style."""
        item_layout = QHBoxLayout()

        # Create a QLabel to represent the line style (solid or dotted)
        line_label = QLabel()
        line_label.setFixedSize(30, 10)
        pixmap = QPixmap(30, 10)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        pen = QPen(color)
        pen.setWidth(2)
        
        # Set line style
        if solid:
            pen.setStyle(Qt.SolidLine)
        else:
            pen.setStyle(Qt.DotLine)

        painter.setPen(pen)
        painter.drawLine(0, 5, 30, 5)
        painter.end()

        line_label.setPixmap(pixmap)

        # Add color description label
        label = QLabel(text)
        item_layout.addWidget(line_label)
        item_layout.addWidget(label)
        layout.addLayout(item_layout)
