import sys
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QSpinBox, QLabel, QPushButton
from PyQt5.QtCore import Qt


class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()  # Load config when initializing
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Rotation angles (in degrees)
        self.rotation_labels = ['Rot X', 'Rot Y', 'Rot Z']
        self.rotation_sliders = []
        self.rotation_spinboxes = []

        for i in range(3):
            slider_layout = QHBoxLayout()

            label = QLabel(self.rotation_labels[i])
            slider_layout.addWidget(label)

            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(-180)
            slider.setMaximum(180)
            slider.setValue(self.config.get(f'rotate_{self.rotation_labels[i][-1].lower()}', 0))  # Set from config
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(10)
            self.rotation_sliders.append(slider)
            slider_layout.addWidget(slider)

            spinbox = QSpinBox()
            spinbox.setRange(-180, 180)
            spinbox.setValue(slider.value())
            spinbox.valueChanged.connect(lambda value, s=slider: s.setValue(value))
            self.rotation_spinboxes.append(spinbox)
            slider.valueChanged.connect(spinbox.setValue)
            slider_layout.addWidget(spinbox)

            layout.addLayout(slider_layout)

        # Translation values (in meters)
        self.translation_labels = ['Trans X', 'Trans Y', 'Trans Z']
        self.translation_sliders = []
        self.translation_spinboxes = []

        for i in range(3):
            slider_layout = QHBoxLayout()

            label = QLabel(self.translation_labels[i])
            slider_layout.addWidget(label)

            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(-500)
            slider.setMaximum(500)
            slider.setValue(self.config.get(f'translate_{self.translation_labels[i][-1].lower()}', 0))  # Set from config
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(10)
            self.translation_sliders.append(slider)
            slider_layout.addWidget(slider)

            spinbox = QSpinBox()
            spinbox.setRange(-500, 500)
            spinbox.setValue(slider.value())
            spinbox.valueChanged.connect(lambda value, s=slider: s.setValue(value))
            self.translation_spinboxes.append(spinbox)
            slider.valueChanged.connect(spinbox.setValue)
            slider_layout.addWidget(spinbox)

            layout.addLayout(slider_layout)

        # Thresholds
        self.threshold_labels = ['X Threshold', 'Y Threshold', 'Z Threshold', 'Movement Threshold']
        self.threshold_sliders = []
        self.threshold_spinboxes = []

        for i in range(4):
            slider_layout = QHBoxLayout()

            label = QLabel(self.threshold_labels[i])
            slider_layout.addWidget(label)

            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(1600)
            slider.setValue(self.config.get(f'{self.threshold_labels[i].lower().replace(" ", "_")}', 50 if i < 3 else 10))
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(10)
            self.threshold_sliders.append(slider)
            slider_layout.addWidget(slider)

            spinbox = QSpinBox()
            spinbox.setRange(0, 1600)
            spinbox.setValue(slider.value())
            spinbox.valueChanged.connect(lambda value, s=slider: s.setValue(value))
            self.threshold_spinboxes.append(spinbox)
            slider.valueChanged.connect(spinbox.setValue)
            slider_layout.addWidget(spinbox)

            layout.addLayout(slider_layout)

        # Add Save Config button
        save_button = QPushButton('Save Config')
        save_button.clicked.connect(self.save_config)  # Connect the button to the save function
        layout.addWidget(save_button)

        self.setLayout(layout)
        self.setWindowTitle('Control Panel')

    def load_config(self):
        # Load config from file or return defaults if file doesn't exist
        if os.path.exists('config.json'):
            with open('config.json', 'r') as config_file:
                return json.load(config_file)
        else:
            return {
                "rotate_x": 0,
                "rotate_y": 0,
                "rotate_z": 0,
                "translate_x": 0,
                "translate_y": 0,
                "translate_z": 0,
                "x_threshold": 5.0,
                "y_threshold": 5.0,
                "z_threshold": 1.4,
                "movement_threshold": 10
            }

    def save_config(self):
        # Gather current values from sliders and spinboxes
        config = {
            "rotate_x": self.rotation_sliders[0].value(),
            "rotate_y": self.rotation_sliders[1].value(),
            "rotate_z": self.rotation_sliders[2].value(),
            "translate_x": self.translation_sliders[0].value(),
            "translate_y": self.translation_sliders[1].value(),
            "translate_z": self.translation_sliders[2].value(),
            "x_threshold": self.threshold_sliders[0].value(),
            "y_threshold": self.threshold_sliders[1].value(),
            "z_threshold": self.threshold_sliders[2].value(),
            "movement_threshold": self.threshold_sliders[3].value()
        }

        # Write the config to a JSON file
        with open('config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)

        print("Config saved to config.json")

