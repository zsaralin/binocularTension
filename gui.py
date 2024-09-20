from PyQt5 import QtWidgets
import sys

class TransformGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Initialize sliders for rotation and translation
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Labels for translation
        self.tx_label = QtWidgets.QLabel('Translate X:')
        self.ty_label = QtWidgets.QLabel('Translate Y:')
        self.tz_label = QtWidgets.QLabel('Translate Z:')
        # Labels for rotation
        self.rx_label = QtWidgets.QLabel('Rotate X:')
        self.ry_label = QtWidgets.QLabel('Rotate Y:')
        self.rz_label = QtWidgets.QLabel('Rotate Z:')

        # Sliders for translation
        self.tx_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.ty_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.tz_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        # Sliders for rotation
        self.rx_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.ry_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.rz_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        # Set ranges for sliders (adjust based on your needs)
        for slider in [self.tx_slider, self.ty_slider, self.tz_slider]:
            slider.setMinimum(-100)
            slider.setMaximum(100)

        for slider in [self.rx_slider, self.ry_slider, self.rz_slider]:
            slider.setMinimum(-180)
            slider.setMaximum(180)

        # Add translation labels and sliders to layout
        layout.addWidget(self.tx_label)
        layout.addWidget(self.tx_slider)
        layout.addWidget(self.ty_label)
        layout.addWidget(self.ty_slider)
        layout.addWidget(self.tz_label)
        layout.addWidget(self.tz_slider)

        # Add rotation labels and sliders to layout
        layout.addWidget(self.rx_label)
        layout.addWidget(self.rx_slider)
        layout.addWidget(self.ry_label)
        layout.addWidget(self.ry_slider)
        layout.addWidget(self.rz_label)
        layout.addWidget(self.rz_slider)

        # Set the layout for the widget
        self.setLayout(layout)

    def get_translation(self):
        return self.tx_slider.value(), self.ty_slider.value(), self.tz_slider.value()

    def get_rotation(self):
        return self.rx_slider.value(), self.ry_slider.value(), self.rz_slider.value()

def run_gui():
    app = QtWidgets.QApplication(sys.argv)
    transform_gui = TransformGUI()
    transform_gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_gui()
