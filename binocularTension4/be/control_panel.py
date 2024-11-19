import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QLineEdit, QScrollArea, QCheckBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
from cube_utils.cube_edit_dialog import CubeEditDialog
from cube_utils.cube_manager import CubeManager
from live_config import LiveConfig
from version import switch_folder_on_server

class ControlPanelWidget(QWidget):
    def __init__(self, parent=None):
        super(ControlPanelWidget, self).__init__(parent)
        self.live_config = LiveConfig.get_instance()

        # Load configuration from file or use defaults
        self.config = self.load_config()
        self.cube_manager = CubeManager.get_instance()
        self.version = [self.config.get("version")]  

        # Initialize settings
        self.rotation = [
            self.config['rotate_x'], self.config['rotate_y'], self.config['rotate_z']
        ]
        self.translation = [
            self.config['translate_x'], self.config['translate_y'], self.config['translate_z']
        ]
        self.divider = [
            self.config['camera_z'], 
            self.config['y_top_divider'], self.config['y_bottom_divider'], 
            self.config['y_top_divider_object'], self.config['y_bottom_divider_object'], 
            self.config['x_divider_angle'], self.config['z_divider'], 
            self.config['z_divider_curve'],
            self.config['y_top_divider_angle'], self.config['y_bottom_divider_angle'], self.config['draw_planes']  # New angles
        ]
        self.movement = [
            self.config['min_contour_area'], self.config['person_movement_thres'], self.config['headpoint_smoothing'], 
            self.config['tracking_hold_duration'], self.config['extended_timeout'], self.config['always_closest']
        ]
        self.smoothing = [
            self.config['stable_thres_x'], self.config['stable_thres_y'], self.config['stable_thres_z']
        ]
        self.point_size = [self.config.get("point_size", 2)]  # Single-item list for point size
        self.num_divisions = [self.config.get("num_divisions", 10)]  # Single-item list for num_divisions

        # Threshold settings
        self.thresholds = [
            self.config.get('x_threshold_min', 0), self.config.get('x_threshold_max', 10),
            self.config.get('y_threshold_min', 0), self.config.get('y_threshold_max', 10),
            self.config.get('z_threshold_min', 0), self.config.get('z_threshold_max', 10)
        ]
        self.detection_type = [self.config.get("detect_people"), self.config.get("detect_objects")]  

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
                "version": "Jade",
                "rotate_x": 0,
                "rotate_y": 0,
                "rotate_z": 0,
                "translate_x": 0,
                "translate_y": 0,
                "translate_z": 0,
                "camera_z": 0,
                "y_top_divider": 0,
                "y_bottom_divider": 0,
                "y_top_divider_object": 0,
                "y_bottom_divider_object": 0,
                "x_divider_angle": 0,
                "z_divider": 0,
                "z_divider_curve": 0,
                "draw_planes": True,
                "y_top_divider_angle": 0,  # Default angle
                "y_bottom_divider_angle": 0,  # Default angle
                "min_contour_area": 500,
                "person_movement_thres": 0.01,
                "headpoint_smoothing": 0.5,
                "tracking_hold_duration": 5,
                "extended_timeout": 2,
                "always_closest": True,
                "point_size": 2,
                "num_divisions": 10,
                "x_threshold_min": 0,
                "x_threshold_max": 10,
                "y_threshold_min": 0,
                "y_threshold_max": 10,
                "z_threshold_min": 0,
                "z_threshold_max": 10,
                "stable_thres_x": 10,
                "stable_thres_y": 0,
                "stable_thres_z": 10,
                "detect_people": True,
                "detect_objects": True
            }

    def save_config(self):
        config = {
            "version": self.version[0],
            "rotate_x": self.rotation[0],
            "rotate_y": self.rotation[1],
            "rotate_z": self.rotation[2],
            "translate_x": self.translation[0],
            "translate_y": self.translation[1],
            "translate_z": self.translation[2],
            "camera_z": self.divider[0],
            "y_top_divider": self.divider[1],
            "y_bottom_divider": self.divider[2],
            "y_top_divider_object": self.divider[3],
            "y_bottom_divider_object": self.divider[4],
            "x_divider_angle": self.divider[5],
            "z_divider": self.divider[6],
            "z_divider_curve": self.divider[7],
            "y_top_divider_angle": self.divider[3],
            "y_bottom_divider_angle": self.divider[4],
            "draw_planes": self.divider[10],
            "y_top_divider_angle": self.divider[8],  # Save top angle
            "y_bottom_divider_angle": self.divider[9],  # Save bottom angle
            "min_contour_area": self.movement[0],
            "person_movement_thres": self.movement[1],
            "headpoint_smoothing": self.movement[2],
            "tracking_hold_duration": self.movement[3],
            "extended_timeout": self.movement[4],
            "always_closest": self.movement[5],
            "point_size": self.point_size[0],
            "num_divisions": self.num_divisions[0],
            "x_threshold_min": self.thresholds[0],
            "x_threshold_max": self.thresholds[1],
            "y_threshold_min": self.thresholds[2],
            "y_threshold_max": self.thresholds[3],
            "z_threshold_min": self.thresholds[4],
            "z_threshold_max": self.thresholds[5],
            "stable_thres_x": self.smoothing[0],
            "stable_thres_y": self.smoothing[1],
            "stable_thres_z": self.smoothing[2],
            "detect_people": self.detection_type[0],
            "detect_objects": self.detection_type[1]
        }
        with open('config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)
        print("Configuration saved.")


    def init_ui(self):
        # Main layout for ControlPanelWidget
        main_layout = QVBoxLayout(self)

        # Create a scroll area and set it up for resizing and scroll behavior
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        
        # Create a widget to contain the layout within the scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Version selection (radio buttons)
        version_label = QLabel("Select Version")
        version_label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(version_label)

    # Create a horizontal layout for the radio buttons
        version_layout = QHBoxLayout()

    # Create radio buttons for "Jade" and "Gab"
        jade_radio = QRadioButton("Jade")
        gab_radio = QRadioButton("Gab")
        
        # Add the radio buttons to the horizontal layout
        version_layout.addWidget(jade_radio)
        version_layout.addWidget(gab_radio)

        # Add the radio buttons to a button group
        version_button_group = QButtonGroup(self)
        version_button_group.addButton(jade_radio)
        version_button_group.addButton(gab_radio)

        # Set "Jade" as the default selected option
        jade_radio.setChecked(True)
        jade_radio.toggled.connect(lambda checked: switch_folder_on_server("jade") if checked else None)
        gab_radio.toggled.connect(lambda checked: switch_folder_on_server("gab") if checked else None)

        # Add the horizontal layout to the main content layout
        content_layout.addLayout(version_layout)
        # Rotation sliders
        label = QLabel("Rotation")
        label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(label)
        self.create_slider_group(content_layout, "Rot X", 0, -180, 180, self.rotation, 0)
        self.create_slider_group(content_layout, "Rot Y", 1, -180, 180, self.rotation, 1)
        self.create_slider_group(content_layout, "Rot Z", 2, -180, 180, self.rotation, 2)

        # Translation sliders
        label = QLabel("Translation")
        label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(label)
        self.create_slider_group(content_layout, "Trans X", 0, -10, 10, self.translation, 0, 0.1)
        self.create_slider_group(content_layout, "Trans Y", 1, -10, 10, self.translation, 1, 0.1)
        self.create_slider_group(content_layout, "Trans Z", 2, -10, 10, self.translation, 2, 0.1)

        # Threshold sliders
        label = QLabel("Thresholds")
        label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(label)
        self.create_slider_group(content_layout, "X Min", 0, -15, 15, self.thresholds, 0, 0.1)
        self.create_slider_group(content_layout, "X Max", 1, -15, 15, self.thresholds, 1, 0.1)
        self.create_slider_group(content_layout, "Y Min", 2, -10, 50, self.thresholds, 2, 0.1)
        self.create_slider_group(content_layout, "Y Max", 3, -10, 50, self.thresholds, 3, 0.1)
        self.create_slider_group(content_layout, "Z Min", 4, -15, 0, self.thresholds, 4, 0.1)
        self.create_slider_group(content_layout, "Z Max", 5, -10, 0, self.thresholds, 5, 0.1)

        # Divider Settings
        label = QLabel("Divider Settings")
        label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(label)
        self.create_slider_group(content_layout, "Camera Z", 0, -15, 15, self.divider, 0, 0.1)
        self.create_slider_group(content_layout, "Top Y Divider", 1, -5, 15, self.divider, 1, 0.01)
        self.create_slider_group(content_layout, "Bottom Y Divider", 2, -5, 15, self.divider, 2, 0.01)
        self.create_slider_group(content_layout, "Top Y Divider Object", 3, -5, 15, self.divider, 3, 0.01)
        self.create_slider_group(content_layout, "Bottom Y Divider Object", 4, -5, 15, self.divider, 4, 0.01)
        self.create_slider_group(content_layout, "X Divider Angle", 5, 0, 360, self.divider, 5, 1)
        self.create_slider_group(content_layout, "Z Divider", 6, -15, 15, self.divider, 6, 0.1)
        self.create_slider_group(content_layout, "Z Divider Curve", 7, 0, 10, self.divider, 7, 1)
        self.create_slider_group(content_layout, "Top Y Divider Angle", 8, -90, 90, self.divider, 8, 1)  # New
        self.create_slider_group(content_layout, "Bottom Y Divider Angle", 9, -90, 90, self.divider, 9, 1) 
        # Draw Planes checkbox
        draw_planes_checkbox = QCheckBox("Draw Planes")
        draw_planes_checkbox.setChecked(True)
        draw_planes_checkbox.stateChanged.connect(lambda state: setattr(self.live_config, 'draw_planes', bool(state)))
        content_layout.addWidget(draw_planes_checkbox)

        # Movement Detection sliders
        label = QLabel("Movement Detection/Tracking")
        label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(label)
        self.create_slider_group(content_layout, "Min Contour Area", 0, 100, 1000, self.movement, 0, 1)
        self.create_slider_group(content_layout, "Person Movement Threshold", 1, 0.01, 10, self.movement, 1, 0.01)
        self.create_slider_group(content_layout, "Headpoint Smoothing", 2, 0, 1, self.movement, 2, 0.1)
        self.create_slider_group(content_layout, "Tracking Hold Duration (s)", 3, 0, 15, self.movement, 3, 1)
        self.create_slider_group(content_layout, "Extended Timeout (s)", 4, 0, 15, self.movement, 4, 1)
        # Draw Planes checkbox
        always_closest_checkbox = QCheckBox("Always Closest")
        always_closest_checkbox.setChecked(self.movement[5])
        always_closest_checkbox.stateChanged.connect(lambda state: setattr(self.live_config, 'always_closest', bool(state)))
        content_layout.addWidget(always_closest_checkbox)

        label = QLabel("Smoothing")
        label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(label)
        self.create_slider_group(content_layout, "X Thres", 0, 0, 100, self.smoothing, 0, 1)
        self.create_slider_group(content_layout, "Y Thres", 1, 0, 100, self.smoothing, 1, 1)
        self.create_slider_group(content_layout, "Z Thres", 2, 0, 100, self.smoothing, 2, 1)

        # Point Size slider
        label = QLabel("Point Cloud Settings")
        label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(label)
        self.create_slider_group(content_layout, "Point Size", 0, 1, 10, self.point_size, 0, 1)

        # Num Divisions slider
        label = QLabel("Grid Settings")
        label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(label)
        self.create_slider_group(content_layout, "Num Divisions", 0, 10, 200, self.num_divisions, 0, 10)

        label = QLabel("Detection Type")
        label.setStyleSheet("font-weight: bold;")
        content_layout.addWidget(label)
        detect_people_checkbox = QCheckBox("Detect People")
        detect_people_checkbox.setChecked(self.detection_type[0])
        detect_people_checkbox.stateChanged.connect(lambda state: setattr(self.live_config, 'detect_people', bool(state)))
        content_layout.addWidget(detect_people_checkbox)

        detect_objects_checkbox = QCheckBox("Detect Objects")
        detect_objects_checkbox.setChecked(self.detection_type[1])
        detect_objects_checkbox.stateChanged.connect(lambda state: setattr(self.live_config, 'detect_objects', bool(state)))
        content_layout.addWidget(detect_objects_checkbox)

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

    def create_slider_group(self, layout, label_text, index, min_val, max_val, target_list, list_index, step=1):
        """Helper function to create a label, slider, and input field, and add them to the layout."""
        hbox = QHBoxLayout()
        
        # Adjust scaling for different step sizes
        scaled_min = int(min_val * 10) if step == 0.1 else int(min_val * 100) if step == 0.01 else min_val
        scaled_max = int(max_val * 10) if step == 0.1 else int(max_val * 100) if step == 0.01 else max_val
        scaled_value = int(target_list[list_index] * 10) if step == 0.1 else int(target_list[list_index] * 100) if step == 0.01 else target_list[list_index]

        # Label and Slider configuration
        label = QLabel(label_text)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(scaled_min)
        slider.setMaximum(scaled_max)
        slider.setValue(scaled_value)
        
        # Value display fields
        value_label = QLabel(f"{target_list[list_index]:.2f}")
        value_label.setAlignment(Qt.AlignRight)

        input_field = QLineEdit(f"{target_list[list_index]:.2f}")
        input_field.setFixedWidth(50)
        input_field.setAlignment(Qt.AlignCenter)

        # Event handling for updating display and values
        input_field.returnPressed.connect(lambda: self.update_slider_from_input(input_field, slider, min_val, max_val, step))
        slider.valueChanged.connect(lambda value, lbl=value_label, inp=input_field: self.update_value_display(lbl, inp, value, step))
        slider.valueChanged.connect(lambda value: self.update_value(index, target_list, value, step))

        # Layout updates
        hbox.addWidget(label)
        hbox.addWidget(slider)
        hbox.addWidget(value_label)
        hbox.addWidget(input_field)
        layout.addLayout(hbox)

    def snap_slider(self, value, slider, step):
        """Snap the slider's value to the nearest multiple of step."""
        if step != 0:
            snapped_value = round(value / step) * step
            if snapped_value != value:
                slider.blockSignals(True)  # Prevent recursive signals
                slider.setValue(snapped_value)
                slider.blockSignals(False)

    def update_slider_from_input(self, input_field, slider, min_val, max_val, step):
        """Update the slider value based on the input field."""
        try:
            input_value = float(input_field.text())
            
            # Adjust input_value based on step size for correct scaling and snapping
            if step == 10:
                input_value = round(input_value / step) * step
            else:
                input_value = min(max(input_value, min_val), max_val)
            
            # Scale input value for the slider and set the slider's value
            scaled_input = int(input_value / step)
            slider.setValue(scaled_input)
            
        except ValueError:
            pass  # Ignore invalid input

    def update_value_display(self, label, input_field, value, step):
        """Update the label and input field showing the current value."""
        scaled_value = round(value / step) * step if step == 10 else value / (10 if step == 0.1 else 100 if step == 0.01 else 1)

        display_value = f"{int(scaled_value)}" if step == 10 else f"{scaled_value:.2f}"
        
        label.setText(display_value)
        input_field.setText(display_value)

    def sync_with_live_config(self):
        self.live_config.version = self.version[0]
        self.live_config.rotate_x = self.rotation[0]
        self.live_config.rotate_y = self.rotation[1]
        self.live_config.rotate_z = self.rotation[2]
        self.live_config.translate_x = self.translation[0]
        self.live_config.translate_y = self.translation[1]
        self.live_config.translate_z = self.translation[2]
        self.live_config.camera_z = self.divider[0]
        self.live_config.y_top_divider = self.divider[1]
        self.live_config.y_bottom_divider = self.divider[2]
        self.live_config.y_top_divider_object = self.divider[3]
        self.live_config.y_bottom_divider_object = self.divider[4]
        self.live_config.x_divider_angle = self.divider[5]
        self.live_config.z_divider = self.divider[6]
        self.live_config.z_divider_curve = self.divider[7]
        self.live_config.y_top_divider_angle = self.divider[8]
        self.live_config.y_bottom_divider_angle = self.divider[9]
        self.live_config.draw_planes = self.divider[10]

        self.live_config.min_contour_area = self.movement[0]
        self.live_config.person_movement_thres = self.movement[1]
        self.live_config.headpoint_smoothing = self.movement[2]
        self.live_config.tracking_hold_duration = self.movement[3]
        self.live_config.extended_timeout = self.movement[4]
        self.live_config.always_closest = self.movement[5]
        self.live_config.point_size = self.point_size[0]
        self.live_config.num_divisions = self.num_divisions[0]
        self.live_config.x_threshold_min = self.thresholds[0]
        self.live_config.x_threshold_max = self.thresholds[1]
        self.live_config.y_threshold_min = self.thresholds[2]
        self.live_config.y_threshold_max = self.thresholds[3]
        self.live_config.z_threshold_min = self.thresholds[4]
        self.live_config.z_threshold_max = self.thresholds[5]
        self.live_config.stable_x_thres = self.smoothing[0]
        self.live_config.stable_y_thres = self.smoothing[1]
        self.live_config.stable_z_thres = self.smoothing[2]
        self.live_config.detect_people = self.detection_type[0]
        self.live_config.detect_objects = self.detection_type[1]

    def update_value(self, index, target_list, value, step):
        """Update live config dynamically when a slider changes."""
        if step == 10:
            target_list[index] = value - value % 10
        else:
            target_list[index] = value / 10 if step == 0.1 else value / 100 if step == 0.01 else value
            
        if target_list == self.rotation:
            setattr(self.live_config, ["rotate_x", "rotate_y", "rotate_z"][index], target_list[index])
        elif target_list == self.translation:
            setattr(self.live_config, ["translate_x", "translate_y", "translate_z"][index], target_list[index])
        elif target_list == self.divider:
            setattr(self.live_config, ["camera_z", "y_top_divider", "y_bottom_divider", "y_top_divider_object", "y_bottom_divider_object", "x_divider_angle", "z_divider", "z_divider_curve", "y_top_divider_angle", "y_bottom_divider_angle"][index], target_list[index])
        elif target_list == self.movement:
            setattr(self.live_config, ["min_contour_area", "person_movement_thres", "headpoint_smoothing", "tracking_hold_duration", "extended_timeout","always_closest"][index], target_list[index])
        elif target_list == self.smoothing:
            setattr(self.live_config, ["stable_x_thres","stable_y_thres","stable_z_thres"][index], target_list[index])
        elif target_list == self.thresholds:
            setattr(self.live_config, ["x_threshold_min", "x_threshold_max", "y_threshold_min", "y_threshold_max", "z_threshold_min", "z_threshold_max"][index], target_list[index])
        elif target_list == self.detection_type:
            setattr(self.live_config, ["detect_people", "detect_objects"][index], target_list[index])
        elif target_list == self.point_size:
            self.live_config.point_size = target_list[index]
        elif target_list == self.num_divisions:
            self.live_config.num_divisions = target_list[index]

