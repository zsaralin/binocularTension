import json
from PyQt5 import QtWidgets, QtCore

CONFIG_FILE = "config.json"  # Path to config file

class TransformGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Initialize the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # Load initial values from the config file
        self.config = self.load_config()

        # Initialize sliders, spin boxes, and movement threshold control
        self.init_ui()

        # Set the main layout for the widget
        self.setLayout(self.main_layout)

    def init_ui(self):
        # Add sliders and spin boxes for translation
        self.tx_slider, self.tx_spinbox = self.create_slider_with_spinbox('Translate X:', -100, 100, initial_value=self.config.get('translate_x', 0))
        self.ty_slider, self.ty_spinbox = self.create_slider_with_spinbox('Translate Y:', -100, 100, initial_value=self.config.get('translate_y', 0))
        self.tz_slider, self.tz_spinbox = self.create_slider_with_spinbox('Translate Z:', -100, 100, initial_value=self.config.get('translate_z', 0))

        # Add sliders and spin boxes for rotation
        self.rx_slider, self.rx_spinbox = self.create_slider_with_spinbox('Rotate X:', -180, 180, initial_value=self.config.get('rotate_x', 0))
        self.ry_slider, self.ry_spinbox = self.create_slider_with_spinbox('Rotate Y:', -180, 180, initial_value=self.config.get('rotate_y', 0))
        self.rz_slider, self.rz_spinbox = self.create_slider_with_spinbox('Rotate Z:', -180, 180, initial_value=self.config.get('rotate_z', 0))

        # Add x, y, and z threshold sliders and spin boxes with initial values from the config
        self.x_threshold_slider, self.x_threshold_spinbox = self.create_double_slider_with_spinbox('X Threshold:', -5.0, 5.0, initial_value=self.config.get('x_threshold', 5.0))
        self.y_threshold_slider, self.y_threshold_spinbox = self.create_double_slider_with_spinbox('Y Threshold:', -5.0, 5.0, initial_value=self.config.get('y_threshold', 5.0))
        self.z_threshold_slider, self.z_threshold_spinbox = self.create_double_slider_with_spinbox('Z Threshold (Depth):', 0.0, 5.0, initial_value=self.config.get('z_threshold', 0.0))

        # Add the movement threshold slider and spin box (new addition)
        self.movement_threshold_slider, self.movement_threshold_spinbox = self.create_slider_with_spinbox('Movement Threshold:', 1, 100, initial_value=self.config.get('movement_threshold', 10))

        # Add a Save button
        self.save_button = QtWidgets.QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_config)
        self.main_layout.addWidget(self.save_button)

    def create_slider_with_spinbox(self, label_text, min_value, max_value, initial_value=0):
        h_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(label_text)
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(min_value, max_value)
        spinbox = QtWidgets.QSpinBox()
        spinbox.setRange(min_value, max_value)

        slider.valueChanged.connect(lambda: spinbox.setValue(slider.value()))
        spinbox.valueChanged.connect(lambda: slider.setValue(spinbox.value()))

        slider.setValue(initial_value)
        spinbox.setValue(initial_value)

        h_layout.addWidget(label)
        h_layout.addWidget(slider)
        h_layout.addWidget(spinbox)
        self.main_layout.addLayout(h_layout)

        return slider, spinbox

    def create_double_slider_with_spinbox(self, label_text, min_value, max_value, initial_value=0.0):
        h_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(label_text)
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(int(min_value * 100), int(max_value * 100))  # Scale for decimal values
        spinbox = QtWidgets.QDoubleSpinBox()
        spinbox.setRange(min_value, max_value)
        spinbox.setSingleStep(0.01)

        slider.valueChanged.connect(lambda: spinbox.setValue(slider.value() / 100))
        spinbox.valueChanged.connect(lambda: slider.setValue(int(spinbox.value() * 100)))

        slider.setValue(int(initial_value * 100))
        spinbox.setValue(initial_value)

        h_layout.addWidget(label)
        h_layout.addWidget(slider)
        h_layout.addWidget(spinbox)
        self.main_layout.addLayout(h_layout)

        return slider, spinbox

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_config(self):
        config = {
            'translate_x': self.tx_slider.value(),
            'translate_y': self.ty_slider.value(),
            'translate_z': self.tz_slider.value(),
            'rotate_x': self.rx_slider.value(),
            'rotate_y': self.ry_slider.value(),
            'rotate_z': self.rz_slider.value(),
            'x_threshold': self.x_threshold_spinbox.value(),
            'y_threshold': self.y_threshold_spinbox.value(),
            'z_threshold': self.z_threshold_spinbox.value(),
            'movement_threshold': self.movement_threshold_slider.value()  # Save movement threshold
        }

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)

        QtWidgets.QMessageBox.information(self, "Settings Saved", "The current settings have been saved to the config file.")

    def get_translation(self):
        return self.tx_slider.value(), self.ty_slider.value(), self.tz_slider.value()

    def get_rotation(self):
        return self.rx_slider.value(), self.ry_slider.value(), self.rz_slider.value()

    def get_thresholds(self):
        return (self.x_threshold_spinbox.value(),
                self.y_threshold_spinbox.value(),
                self.z_threshold_spinbox.value())

    def get_movement_threshold(self):
        return self.movement_threshold_slider.value()

