import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtCore import Qt
from OpenGL.GL import *
from OpenGL.GLU import *
from glwidget import GLWidget  # Import the GLWidget class

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("PyQt5 OpenGL 3D Cube with Side Panels")

        # Create the main layout
        main_layout = QHBoxLayout()

        # Left section: buttons
        left_panel = QVBoxLayout()
        button1 = QPushButton("Button 1")
        button2 = QPushButton("Button 2")
        button3 = QPushButton("Button 3")
        left_panel.addWidget(button1)
        left_panel.addWidget(button2)
        left_panel.addWidget(button3)

        # Middle section: OpenGL widget
        self.gl_widget = GLWidget(self)

        # Right section: Blue panel
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: blue;")
        right_panel.setFixedWidth(150)

        # Add the three sections to the main layout
        main_layout.addLayout(left_panel)
        main_layout.addWidget(self.gl_widget)
        main_layout.addWidget(right_panel)

        # Create a container widget and set the main layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1280, 480)
    window.show()
    sys.exit(app.exec_())
