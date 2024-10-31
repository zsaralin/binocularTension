import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QLineEdit, QScrollArea, QCheckBox
)
from PyQt5.QtCore import Qt
from cube_utils.cube_edit_dialog import CubeEditDialog
from cube_utils.cube_manager import CubeManager
from live_config import LiveConfig

class ControlPanelWidget(QWidget):
    def __init__(self, parent=None):
        super(ControlPanelWidget, self).__init__(parent)
        self.live_config = LiveConfig.get_instance()

        # Load configuration from file or use defaults
        self.config = self.load_config()
        self.cube_manager = CubeManager.get_instance()

        # Initialize settings
        self.rotation = [
            self.config['rotate_x'], self.config['rotate_y'], self.config['rotate_z']
        ]
        self.translation = [
            self.config['translate_x'], self.config['translate_y'], self.config['translate_z']
        ]
        self.divider = [
            self.config['y_top_divider'], self.config['y_bottom_divider'], 
            self.config['x_divider_angle'], self.config['z_divider'], self.config['z_divider_curve'], self.config['draw_planes']
        ]
        self.movement = [
            self.config['min_contour_area'], self.config['person_movement_thres']
        ]
        self.point_size = [self.config.get("point_size", 2)]  # Single-item list for point size
        self.num_divisions = [self.config.get("num_divisions", 10)]  # Single-item list for num_divisions

        # Threshold settings
        self.thresholds = [
            self.config.get('x_threshold_min', 0), self.config.get('x_threshold_max', 10),
            self.config.get('y_threshold_min', 0), self.config.get('y_threshold_max', 10),
            self.config.get('z_threshold_min', 0), self.config.get('z_threshold_max', 10)
        ]

        # Set up the scrollable layout and UI elements
        self.init_ui()
        self.sync_with_live_config()

    def load_config(self):
        if os.path.exists('config.json'):
            with open('config.json', 'r') as config_file:
                return json.load(config_file)
        else:
            # Defaults for config parameters
            return {
                "rotate_x": 0,
                "rotate_y": 0,
                "rotate_z": 0,
                "translate_x": 0,
                "translate_y": 0,
                "translate_z": 0,
                "y_top_divider": 0,
                "y_bottom_divider": 0,
                "x_divider_angle": 0,
                "z_divider": 0,
                "z_divider_curve": 0,
                "draw_planes": True,
                "min_contour_area": 500,
                "person_movement_thres": 0.01,
                "point_size": 2,  # Default point size
                "num_divisions": 10,  # Default number of divisions
                "x_threshold_min": 0,
                "x_threshold_max": 10,
                "y_threshold_min": 0,
                "y_threshold_max": 10,
                "z_threshold_min": 0,
                "z_threshold_max": 10
            }

    def save_config(self):
        config = {
            "rotate_x": self.rotation[0],
            "rotate_y": self.rotation[1],
            "rotate_z": self.rotation[2],
            "translate_x": self.translation[0],
            "translate_y": self.translation[1],
            "translate_z": self.translation[2],
            "y_top_divider": self.divider[0],
            "y_bottom_divider": self.divider[1],
            "x_divider_angle": self.divider[2],
            "z_divider": self.divider[3],
            "z_divider_curve": self.divider[4],
            "draw_planes": self.divider[5],
            "min_contour_area": self.movement[0],
            "person_movement_thres": self.movement[1],
            "point_size": self.point_size[0],  # Save the point size setting
            "num_divisions": self.num_divisions[0],  # Save the num_divisions setting
            "x_threshold_min": self.thresholds[0],
            "x_threshold_max": self.thresholds[1],
            "y_threshold_min": self.thresholds[2],
            "y_threshold_max": self.thresholds[3],
            "z_threshold_min": self.thresholds[4],
            "z_threshold_max": self.thresholds[5]
        }

        with open('config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)
        print("Config saved to config.json")

    def init_ui(self):
        # Main layout for ControlPanelWidget
        main_layout = QVBoxLayout(self)

        # Create a scroll area and set it up for resizing and scroll behavior
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        
        # Create a widget to contain the layout within the scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Rotation sliders
        content_layout.addWidget(QLabel("Rotation"))
        self.create_slider_group(content_layout, "Rot X", 0, -180, 180, self.rotation, 0)
        self.create_slider_group(content_layout, "Rot Y", 1, -180, 180, self.rotation, 1)
        self.create_slider_group(content_layout, "Rot Z", 2, -180, 180, self.rotation, 2)

        # Translation sliders
        content_layout.addWidget(QLabel("Translation"))
        self.create_slider_group(content_layout, "Trans X", 0, -10, 10, self.translation, 0, 0.1)
        self.create_slider_group(content_layout, "Trans Y", 1, -10, 10, self.translation, 1, 0.1)
        self.create_slider_group(content_layout, "Trans Z", 2, -10, 10, self.translation, 2, 0.1)

        # Threshold sliders
        content_layout.addWidget(QLabel("Thresholds"))
        self.create_slider_group(content_layout, "X Min", 0, -15, 15, self.thresholds, 0, 0.1)
        self.create_slider_group(content_layout, "X Max", 1, -15, 15, self.thresholds, 1, 0.1)
        self.create_slider_group(content_layout, "Y Min", 2, -10, 50, self.thresholds, 2, 0.1)
        self.create_slider_group(content_layout, "Y Max", 3, -10, 50, self.thresholds, 3, 0.1)
        self.create_slider_group(content_layout, "Z Min", 4, -15, 0, self.thresholds, 4, 0.1)
        self.create_slider_group(content_layout, "Z Max", 5, -10, 0, self.thresholds, 5, 0.1)

        # Divider Settings
        content_layout.addWidget(QLabel("Divider Settings"))
        self.create_slider_group(content_layout, "Top Y Divider", 0, -5, 15, self.divider, 0, 0.1)
        self.create_slider_group(content_layout, "Bottom Y Divider", 1, -5, 15, self.divider, 1, 0.1)
        self.create_slider_group(content_layout, "X Divider Angle", 2, 10, 90, self.divider, 2, 1)
        self.create_slider_group(content_layout, "Z Divider", 3, -15, 15, self.divider, 3, 0.1)
        self.create_slider_group(content_layout, "Z Divider Curve", 4, 0, 10, self.divider, 4, 1)

        # Draw Planes checkbox
        draw_planes_checkbox = QCheckBox("Draw Planes")
        draw_planes_checkbox.setChecked(self.divider[5])
        draw_planes_checkbox.stateChanged.connect(self.toggle_draw_planes)
        content_layout.addWidget(draw_planes_checkbox)

        # Movement Detection sliders
        content_layout.addWidget(QLabel("Movement Detection"))
        self.create_slider_group(content_layout, "Min Contour Area", 0, 100, 1000, self.movement, 0, 1)
        self.create_slider_group(content_layout, "Person Movement Threshold", 1, 0.01, 1, self.movement, 1, 0.01)

        # Point Size slider
        content_layout.addWidget(QLabel("Point Cloud Settings"))
        self.create_slider_group(content_layout, "Point Size", 0, 1, 10, self.point_size, 0, 1)

        # Num Divisions slider
        content_layout.addWidget(QLabel("Grid Settings"))
        self.create_slider_group(content_layout, "Num Divisions", 0, 10, 200, self.num_divisions, 0, 10)

        # Cube-related buttons
        edit_cubes_button = QPushButton("Edit Cubes")
        edit_cubes_button.clicked.connect(self.open_edit_cubes_dialog)
        content_layout.addWidget(edit_cubes_button)

        save_cube_button = QPushButton("Save Cubes")
        save_cube_button.clicked.connect(self.cube_manager.save_cubes)
        content_layout.addWidget(save_cube_button)
        # Save button
        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        content_layout.addWidget(save_button)

        # Set content layout to the content widget
        content_widget.setLayout(content_layout)

        # Add content widget to the scroll area
        scroll_area.setWidget(content_widget)

        # Add scroll area to the main layout
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def open_edit_cubes_dialog(self):
        """Opens the CubeEditDialog to edit cube parameters."""
        dialog = CubeEditDialog(self.cube_manager)
        dialog.exec_()

    def toggle_draw_planes(self, state):
        """Toggle the drawing of planes on the point cloud."""
        self.live_config.draw_planes = bool(state)

    def create_slider_group(self, layout, label_text, index, min_val, max_val, target_list, list_index, step=1):
        """Helper function to create a label, slider, and input field, and add them to the layout."""
        hbox = QHBoxLayout()
        
        scaled_min = int(min_val * 10) if step == 0.1 else int(min_val * 100) if step == 0.01 else min_val
        scaled_max = int(max_val * 10) if step == 0.1 else int(max_val * 100) if step == 0.01 else max_val
        scaled_value = int(target_list[list_index] * 10) if step == 0.1 else int(target_list[list_index] * 100) if step == 0.01 else target_list[list_index]

        label = QLabel(label_text)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(scaled_min)
        slider.setMaximum(scaled_max)
        slider.setValue(scaled_value)

        value_label = QLabel(f"{target_list[list_index]:.2f}")
        value_label.setAlignment(Qt.AlignRight)

        input_field = QLineEdit(f"{target_list[list_index]:.2f}")
        input_field.setFixedWidth(50)
        input_field.setAlignment(Qt.AlignCenter)

        input_field.returnPressed.connect(lambda: self.update_slider_from_input(input_field, slider, min_val, max_val, step))
        slider.valueChanged.connect(lambda value, lbl=value_label, inp=input_field: self.update_value_display(lbl, inp, value, min_val, max_val, step))
        slider.valueChanged.connect(lambda value: self.update_value(index, target_list, value, step))

        hbox.addWidget(label)
        hbox.addWidget(slider)
        hbox.addWidget(value_label)
        hbox.addWidget(input_field)
        layout.addLayout(hbox)

    def sync_with_live_config(self):
        self.live_config.rotate_x = self.rotation[0]
        self.live_config.rotate_y = self.rotation[1]
        self.live_config.rotate_z = self.rotation[2]
        self.live_config.translate_x = self.translation[0]
        self.live_config.translate_y = self.translation[1]
        self.live_config.translate_z = self.translation[2]
        self.live_config.y_top_divider = self.divider[0]
        self.live_config.y_bottom_divider = self.divider[1]
        self.live_config.x_divider_angle = self.divider[2]
        self.live_config.z_divider = self.divider[3]
        self.live_config.z_divider_curve = self.divider[4]
        self.live_config.draw_planes = self.divider[5]
        self.live_config.min_contour_area = self.movement[0]
        self.live_config.person_movement_thres = self.movement[1]
        self.live_config.point_size = self.point_size[0]
        self.live_config.num_divisions = self.num_divisions[0]
        self.live_config.x_threshold_min = self.thresholds[0]
        self.live_config.x_threshold_max = self.thresholds[1]
        self.live_config.y_threshold_min = self.thresholds[2]
        self.live_config.y_threshold_max = self.thresholds[3]
        self.live_config.z_threshold_min = self.thresholds[4]
        self.live_config.z_threshold_max = self.thresholds[5]

    def update_value_display(self, label, input_field, value, min_val, max_val, step):
        """Update the label and input field showing the current value."""
        scaled_value = value / 10 if step == 0.1 else value / 100 if step == 0.01 else value
        label.setText(f"{scaled_value:.2f}")
        input_field.setText(f"{scaled_value:.2f}")

    def update_value(self, index, target_list, value, step):
        """Update live config dynamically when a slider changes."""
        target_list[index] = value / 10 if step == 0.1 else value / 100 if step == 0.01 else value
        if target_list == self.rotation:
            setattr(self.live_config, ["rotate_x", "rotate_y", "rotate_z"][index], target_list[index])
        elif target_list == self.translation:
            setattr(self.live_config, ["translate_x", "translate_y", "translate_z"][index], target_list[index])
        elif target_list == self.divider:
            setattr(self.live_config, ["y_top_divider", "y_bottom_divider", "x_divider_angle", "z_divider", "z_divider_curve"][index], target_list[index])
        elif target_list == self.movement:
            setattr(self.live_config, ["min_contour_area", "person_movement_thres"][index], target_list[index])
        elif target_list == self.thresholds:
            setattr(self.live_config, ["x_threshold_min", "x_threshold_max", "y_threshold_min", "y_threshold_max", "z_threshold_min", "z_threshold_max"][index], target_list[index])
        elif target_list == self.point_size:
            self.live_config.point_size = target_list[index]
        elif target_list == self.num_divisions:
            self.live_config.num_divisions = target_list[index]
