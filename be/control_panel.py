import json
import os
import socket
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, 
    QLineEdit, QScrollArea, QCheckBox, QTabWidget
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread
from cube_utils.cube_edit_dialog import CubeEditDialog
from cube_utils.cube_manager import CubeManager
from live_config import LiveConfig
from pynput import keyboard
from frontend_controls_tab import FrontendControlsTab
from slider_value_handler import SliderValueHandler

from preset_listener_service import PresetListenerService

class KeySignalEmitter(QObject):
    """Signal emitter for global keyboard events.
    
    @brief Emits signals when specific keys are pressed globally.
    @var key_pressed: Signal emitted with the pressed key character.
    """
    key_pressed = pyqtSignal(str)

class ControlPanelWidget(QWidget):
    """Main control panel widget for configuration management.
    
    @brief Provides UI controls for various system parameters and configurations - most of this code handles the backend, but the frontend settings is inserted into the panel here as well.
    @details Handles configuration loading/saving, UI setup, and real-time updates.
    """

    def __init__(self, parent=None):
        """Initialize the control panel with configuration and UI setup.
        
        @param parent: Parent widget (default: None)
        """
        super(ControlPanelWidget, self).__init__(parent)
        self.value_handler = SliderValueHandler()
        self.live_config = LiveConfig.get_instance()
        self.cube_manager = CubeManager.get_instance()
        self.window_front = False

        self.preset_listener = PresetListenerService()
        self.preset_listener.value_received.connect(self.update_from_live_config)
        self.preset_listener.start()

        # Configuration initialization
        self._initialize_configuration()
        
        # UI setup
        self.init_ui()
        self.sync_with_live_config()
        
        # Global key listener setup
        self._init_global_key_listener()

    def update_from_live_config(self):
        """
        Update all GUI elements to reflect current LiveConfig values.
        
        This method synchronizes the GUI state with the LiveConfig singleton,
        updating all sliders, checkboxes, and input fields to match the current
        configuration values. The method finds all QHBoxLayouts containing QSliders
        and updates them based on their label text.
        """
        # First update our internal lists from LiveConfig
        if hasattr(self, 'rotation'):
            self.rotation[0] = self.live_config.rotate_x
            self.rotation[1] = self.live_config.rotate_y
            self.rotation[2] = self.live_config.rotate_z
            
        if hasattr(self, 'translation'):
            self.translation[0] = self.live_config.translate_x
            self.translation[1] = self.live_config.translate_y
            self.translation[2] = self.live_config.translate_z
            
        if hasattr(self, 'thresholds'):
            self.thresholds[0] = self.live_config.x_threshold_min
            self.thresholds[1] = self.live_config.x_threshold_max
            self.thresholds[2] = self.live_config.y_threshold_min
            self.thresholds[3] = self.live_config.y_threshold_max
            self.thresholds[4] = self.live_config.z_threshold_min
            self.thresholds[5] = self.live_config.z_threshold_max
            
        if hasattr(self, 'divider'):
            self.divider[0] = self.live_config.camera_z
            self.divider[1] = self.live_config.y_top_divider
            self.divider[2] = self.live_config.y_bottom_divider
            self.divider[3] = self.live_config.x_divider_angle
            self.divider[4] = self.live_config.y_top_divider_angle
            self.divider[5] = self.live_config.y_bottom_divider_angle
            self.divider[6] = self.live_config.draw_planes
            
        if hasattr(self, 'movement'):
            self.movement[0] = self.live_config.min_contour_area
            self.movement[1] = self.live_config.movement_thres
            self.movement[2] = self.live_config.headpoint_smoothing
            self.movement[3] = self.live_config.active_object_stick_time
            self.movement[4] = self.live_config.conf_thres
            self.movement[5] = self.live_config.stationary_timeout
            self.movement[6] = self.live_config.roi_filter_dur
            
        if hasattr(self, 'smoothing'):
            self.smoothing[0] = self.live_config.stable_x_thres
            self.smoothing[1] = self.live_config.stable_y_thres
            
        if hasattr(self, 'point_size'):
            self.point_size[0] = self.live_config.point_size
            
        if hasattr(self, 'num_divisions'):
            self.num_divisions[0] = self.live_config.num_divisions
            
        if hasattr(self, 'detection_type'):
            self.detection_type[0] = self.live_config.detect_people
            self.detection_type[1] = self.live_config.detect_objects

        # Update all slider groups in the UI
        # Each slider group is in a QHBoxLayout containing a QLabel, QSlider, QLabel, QLineEdit
        for hbox in self.findChildren(QHBoxLayout):
            # Get all widgets in this horizontal layout
            widgets = [hbox.itemAt(i).widget() for i in range(hbox.count()) if hbox.itemAt(i)]
            
            # Look for layouts matching our slider group pattern
            if len(widgets) == 4:  # Label + Slider + ValueLabel + LineEdit
                label, slider, value_label, line_edit = widgets
                if isinstance(label, QLabel) and isinstance(slider, QSlider):
                    label_text = label.text()
                    # Find the correct list and index based on the label text
                    value = self._get_value_from_label(label_text)
                    if value is not None:
                        step = self._get_step_for_label(label_text)
                        # Scale value for slider 
                        scaled_value = int(value / step)
                        slider.setValue(scaled_value)
                        # Update value displays
                        display_value = f"{value:.2f}" if step < 1 else f"{int(value)}"
                        value_label.setText(display_value)
                        line_edit.setText(display_value)

        # Update checkboxes
        for checkbox in self.findChildren(QCheckBox):
            if checkbox.text() == "Draw Planes":
                checkbox.setChecked(self.live_config.draw_planes)
            elif checkbox.text() == "Detect Yolo Objects":
                checkbox.setChecked(self.live_config.detect_people)
            elif checkbox.text() == "Detect Other Objects":
                checkbox.setChecked(self.live_config.detect_objects)

    def _get_value_from_label(self, label_text):
        """
        Get the appropriate value based on the slider's label text.
        
        @param label_text: The text label of the slider
        @return: The current value for that control or None if not found
        """
        # Map of label texts to their corresponding list and index
        label_map = {
            "Rot X": (self.rotation, 0),
            "Rot Y": (self.rotation, 1),
            "Rot Z": (self.rotation, 2),
            "Trans X": (self.translation, 0),
            "Trans Y": (self.translation, 1),
            "Trans Z": (self.translation, 2),
            "X Min": (self.thresholds, 0),
            "X Max": (self.thresholds, 1),
            "Y Min": (self.thresholds, 2),
            "Y Max": (self.thresholds, 3),
            "Z Min": (self.thresholds, 4),
            "Z Max": (self.thresholds, 5),
            "Camera Z": (self.divider, 0),
            "Top Y Divider": (self.divider, 1),
            "Bottom Y Divider": (self.divider, 2),
            "X Divider Angle": (self.divider, 3),
            "Top Y Divider Angle": (self.divider, 4),
            "Bottom Y Divider Angle": (self.divider, 5),
            "Min Contour Area": (self.movement, 0),
            "Movement Threshold": (self.movement, 1),
            "Headpoint Smoothing": (self.movement, 2),
            "Active Object Stick Time": (self.movement, 3),
            "Conf Thres": (self.movement, 4),
            "Stationary Timeout": (self.movement, 5),
            "ROI Filter Dur": (self.movement, 6),
            "X Thres": (self.smoothing, 0),
            "Y Thres": (self.smoothing, 1),
            "Point Size": (self.point_size, 0),
            "Num Divisions": (self.num_divisions, 0)
        }
        
        if label_text in label_map:
            target_list, index = label_map[label_text]
            return target_list[index]
        return None

    def _get_step_for_label(self, label_text):
        """
        Get the step size for a slider based on its label.
        
        @param label_text: The text label of the slider
        @return: Step size for the slider (default: 1)
        """
        # Map of labels to their step sizes
        step_map = {
            "Trans X": 0.01,
            "Trans Y": 0.01,
            "Trans Z": 0.01,
            "Top Y Divider": 0.01,
            "Bottom Y Divider": 0.01,
            "Headpoint Smoothing": 0.1,
            "Conf Thres": 0.1
        }
        return step_map.get(label_text, 1)
                
    def _get_value_for_slider(self, slider_name):
        """
        Get the current value for a slider from its corresponding list.
        
        @param slider_name: Name of the slider to look up
        @return: Current value for the slider or None if not found
        """
        # Map slider names to their corresponding list and index
        value_maps = {
            'rotate_x': (self.rotation, 0),
            'rotate_y': (self.rotation, 1),
            'rotate_z': (self.rotation, 2),
            'translate_x': (self.translation, 0),
            'translate_y': (self.translation, 1),
            'translate_z': (self.translation, 2),
            # Add more mappings as needed
        }
        
        if slider_name in value_maps:
            target_list, index = value_maps[slider_name]
            return target_list[index]
        return None
        
    def _get_step_for_slider(self, slider_name):
        """
        Get the step size for a slider based on its name.
        
        @param slider_name: Name of the slider to look up
        @return: Step size for the slider (default: 1)
        """
        # Map slider names to their step sizes
        step_maps = {
            'translate_x': 0.01,
            'translate_y': 0.01,
            'translate_z': 0.01,
            'headpoint_smoothing': 0.1,
            'conf_thres': 0.1,
        }
        
        return step_maps.get(slider_name, 1)
    
                
    def _get_value_for_slider(self, slider_name):
        """
        Get the current value for a slider from its corresponding list.
        
        @param slider_name: Name of the slider to look up
        @return: Current value for the slider or None if not found
        """
        # Map slider names to their corresponding list and index
        value_maps = {
            'rotate_x': (self.rotation, 0),
            'rotate_y': (self.rotation, 1),
            'rotate_z': (self.rotation, 2),
            'translate_x': (self.translation, 0),
            'translate_y': (self.translation, 1),
            'translate_z': (self.translation, 2),
            # Add more mappings as needed
        }
        
        if slider_name in value_maps:
            target_list, index = value_maps[slider_name]
            return target_list[index]
        return None
        
    def _get_step_for_slider(self, slider_name):
        """
        Get the step size for a slider based on its name.
        
        @param slider_name: Name of the slider to look up
        @return: Step size for the slider (default: 1)
        """
        # Map slider names to their step sizes
        step_maps = {
            'translate_x': 0.01,
            'translate_y': 0.01,
            'translate_z': 0.01,
            'headpoint_smoothing': 0.1,
            'conf_thres': 0.1,
        }
        
        return step_maps.get(slider_name, 1)




    def _initialize_configuration(self):
        """Load and initialize configuration parameters from file or defaults."""
        self.config = self.load_config()
        self.version = [self.config.get("version")]
        
        # Parameter groups initialization
        self.rotation = [
            self.config['rotate_x'], 
            self.config['rotate_y'], 
            self.config['rotate_z']
        ]
        self.translation = [
            self.config['translate_x'], 
            self.config['translate_y'], 
            self.config['translate_z']
        ]
        self.divider = [
            self.config['camera_z'], 
            self.config['y_top_divider'], 
            self.config['y_bottom_divider'],
            self.config['x_divider_angle'], 
            self.config['y_top_divider_angle'],
            self.config['y_bottom_divider_angle'], 
            self.config['draw_planes']
        ]
        self.movement = [
            self.config['min_contour_area'], 
            self.config['movement_thres'],
            self.config['headpoint_smoothing'],
            self.config['active_object_stick_time'],
            self.config['conf_thres'],
            self.config["stationary_timeout"],
            self.config["roi_filter_dur"]
        ]
        self.smoothing = [
            self.config['stable_thres_x'], 
            self.config['stable_thres_y']
        ]
        self.point_size = [self.config.get("point_size", 2)]
        self.num_divisions = [self.config.get("num_divisions", 10)]
        self.thresholds = [
            self.config.get('x_threshold_min', 0), 
            self.config.get('x_threshold_max', 10),
            self.config.get('y_threshold_min', 0), 
            self.config.get('y_threshold_max', 10),
            self.config.get('z_threshold_min', 0), 
            self.config.get('z_threshold_max', 10)
        ]
        self.detection_type = [
            self.config.get("detect_people", True), 
            self.config.get("detect_objects", True)
        ]

    def _init_global_key_listener(self):
        """Initialize global keyboard listener in a separate thread."""
        self.key_emitter = KeySignalEmitter()
        self.key_emitter.key_pressed.connect(self.handle_global_key)
        
        self.listener_thread = QThread()
        self.listener_thread.start()

        def start_listener():
            with keyboard.Listener(on_press=self._on_key_press) as listener:
                listener.join()

        self.listener_thread.run = start_listener
        self.listener_thread.start()

    def _on_key_press(self, key):
        """Handle key press events from global listener.
        
        @param key: The pressed key object from pynput
        """
        try:
            if key.char == 'g':
                self.key_emitter.key_pressed.emit('g')
        except AttributeError:
            pass

    def handle_global_key(self, key):
        """Handle key events in main GUI thread.
        
        @param key: Character of the pressed key
        """
        if key == 'g':
            self.toggle_window()

    def _bring_to_front(self):
        """Bring window to foreground and ensure it's visible."""
        print("Bringing window to front")
        window = self.window()
        window.show()  # Make sure window is visible
        window.raise_()  # Bring it to the top
        window.activateWindow()  # Give it keyboard focus
            
    def focusOutEvent(self, event):
        """Handle window losing focus - update window_front state."""
        print("Focus lost")
        self.window_front = False
        super().focusOutEvent(event)

    def isWindowActive(self):
        """Check if window is currently the active window."""
        return self.window().isActiveWindow()
        
    def toggle_window(self):
        """Toggle window visibility state."""
        window = self.window()
        
        # Check if window is visible and on top
        is_top_window = window.windowFlags() & Qt.WindowStaysOnTopHint
        
        if not is_top_window:
            # Bring to front
            window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)
            window.show()
            window.raise_()
            window.activateWindow()
        else:
            # Remove stay on top flag and lower
            window.setWindowFlags(window.windowFlags() & ~Qt.WindowStaysOnTopHint)
            window.show()
            window.lower()
            # Send socket message to bring frontend to front
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    message = {
                        "variable": "focus_command",
                        "value": 1
                    }
                    sock.sendto(json.dumps(message).encode(), ('localhost', 12345))
            except Exception as e:
                print(f"Error sending focus command: {e}")

    def _send_to_back(self):
        """Send window to background and minimize."""
        window = self.window()
        window.setWindowState(window.windowState() | Qt.WindowMinimized)

    def closeEvent(self, event):
        """Clean up resources on window close.
        
        @param event: Close event object
        """
        self.listener_thread.quit()
        self.listener_thread.wait()
        self.preset_listener.stop()
        super().closeEvent(event)

    def load_config(self):
        """Load configuration from file or return defaults.
        
        @return: Dictionary containing configuration parameters
        """
        if os.path.exists('config.json'):
            with open('config.json', 'r') as config_file:
                config = json.load(config_file)
                config['translate_x'] = config.get('translate_x', 0)
                config['translate_y'] = config.get('translate_y', 0)
                config['translate_z'] = config.get('translate_z', 0)
                return config
                
        return {
            # Default configuration values
            "version": "Brown",
            "rotate_x": 0, "rotate_y": 0, "rotate_z": 0,
            "translate_x": 0, "translate_y": 0, "translate_z": 0,
            "camera_z": 0, "y_top_divider": 0, "y_bottom_divider": 0,
            "x_divider_angle": 0, "draw_planes": True,
            "y_top_divider_angle": 0, "y_bottom_divider_angle": 0,
            "min_contour_area": 500, "movement_thres": 10,
            "headpoint_smoothing": 0.5, "active_object_stick_time": 3,
            "conf_thres": .1, "stationary_timeout": 20, "roi_filter_dur": 10,
            "point_size": 2, "num_divisions": 10,
            "x_threshold_min": 0, "x_threshold_max": 10,
            "y_threshold_min": 0, "y_threshold_max": 10,
            "z_threshold_min": 0, "z_threshold_max": 10,
            "stable_thres_x": 10, "stable_thres_y": 0,
            "detect_people": True, "detect_objects": True
        }


    def save_config(self):
        """Save current configuration to config file."""
        config_data = {
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
            "x_divider_angle": self.divider[3],
            "draw_planes": self.divider[6],
            "y_top_divider_angle": self.divider[4],
            "y_bottom_divider_angle": self.divider[5],
            "min_contour_area": self.movement[0],
            "movement_thres": self.movement[1],
            "headpoint_smoothing": self.movement[2],
            "active_object_stick_time": self.movement[3],
            "conf_thres": self.movement[4],
            "stationary_timeout": self.movement[5],
            "roi_filter_dur": self.movement[6],
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
            "detect_people": self.detection_type[0],
            "detect_objects": self.detection_type[1]
        }

        try:
            print("Translation values being saved:", self.translation)
            with open('config.json', 'w') as f:
                json.dump(config_data, f, indent=4)
            print("Configuration saved successfully")
        except Exception as e:
            print(f"Error saving configuration: {e}")


    def init_ui(self):
        """Initialize and arrange UI components."""
        main_layout = QVBoxLayout(self)
        tab_widget = QTabWidget()

        # Main controls tab
        main_tab = self._create_main_controls_tab()
        tab_widget.addTab(main_tab, "Backend Controls")

        # Frontend controls tab
        frontend_tab = FrontendControlsTab()
        tab_widget.addTab(frontend_tab, "Frontend Controls")

        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)

    def _create_main_controls_tab(self):
        """Create and configure the main controls tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Add control sections
        self._add_rotation_controls(content_layout)
        self._add_translation_controls(content_layout)
        self._add_threshold_controls(content_layout)
        self._add_divider_controls(content_layout)
        self._add_movement_controls(content_layout)
        self._add_smoothing_controls(content_layout)
        self._add_point_cloud_controls(content_layout)
        self._add_detection_controls(content_layout)
        self._add_action_buttons(content_layout)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        return tab
    
    def _add_rotation_controls(self, layout):
        """Add rotation controls to the layout."""
        self._add_section_header(layout, "Rotation")
        self._create_slider_group(layout, "Rot X", 0, -180, 180, self.rotation, 0)
        self._create_slider_group(layout, "Rot Y", 1, -180, 180, self.rotation, 1)
        self._create_slider_group(layout, "Rot Z", 2, -180, 180, self.rotation, 2)

    def _add_translation_controls(self, layout):
        """Add translation control sliders."""
        self._add_section_header(layout, "Translation")
        self._create_slider_group(layout, "Trans X", 0, -10, 10, self.translation, 0, 0.01)
        self._create_slider_group(layout, "Trans Y", 1, -10, 10, self.translation, 1, 0.01)
        self._create_slider_group(layout, "Trans Z", 2, -10, 10, self.translation, 2, 0.01)


    def open_edit_cubes_dialog(self):
        """Opens the CubeEditDialog to edit cube parameters."""
        dialog = CubeEditDialog(self.cube_manager)
        dialog.exec_()

    def _create_slider_group(self, layout, label_text, index, min_val, max_val, target_list, list_index, step=1):
        """
        Create a slider group with label, slider, and input field.
        
        @param layout: Layout to add the slider group to
        @param label_text: Text label for the slider
        @param index: Index for value updates
        @param min_val: Minimum value
        @param max_val: Maximum value
        @param target_list: List containing the target value
        @param list_index: Index in the target list
        @param step: Step size for value changes (default: 1)
        """
        hbox = QHBoxLayout()
        
        # Convert current value to slider position
        current_value = target_list[list_index]
        slider_pos = self.value_handler.to_slider_value(current_value, step)
        
        # Convert min/max to slider positions
        slider_min = self.value_handler.to_slider_value(min_val, step)
        slider_max = self.value_handler.to_slider_value(max_val, step)
        
        # Create UI elements
        label = QLabel(label_text)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(slider_min, slider_max)
        slider.setValue(slider_pos)
        
        # Format display value
        display_value = self.value_handler.format_display_value(current_value, step)
        value_label = QLabel(display_value)
        input_field = QLineEdit(display_value)
        input_field.setFixedWidth(50)

        def on_slider_changed(slider_pos):
            """Handle slider value changes."""
            # Convert slider position to actual value
            actual_value = self.value_handler.from_slider_value(slider_pos, step)
            
            # Update displays
            formatted_value = self.value_handler.format_display_value(actual_value, step)
            value_label.setText(formatted_value)
            input_field.setText(formatted_value)
            
            # Store actual value
            target_list[list_index] = actual_value
            self.update_value(index, target_list, actual_value, step)

        def on_input_changed():
            """Handle direct input value changes."""
            try:
                input_value = float(input_field.text())
                if min_val <= input_value <= max_val:
                    # Convert input to slider position
                    slider_pos = self.value_handler.to_slider_value(input_value, step)
                    slider.setValue(slider_pos)
                    # Store the actual value
                    target_list[list_index] = input_value
                    self.update_value(index, target_list, input_value, step)
            except ValueError:
                pass

        slider.valueChanged.connect(on_slider_changed)
        input_field.returnPressed.connect(on_input_changed)
        
        hbox.addWidget(label)
        hbox.addWidget(slider)
        hbox.addWidget(value_label)
        hbox.addWidget(input_field)
        layout.addLayout(hbox)

    def _add_section_header(self, layout, text):
        """Add a section header to the layout.
        
        @param layout: Target layout to add header to
        @param text: Header text content
        """
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

    def _add_threshold_controls(self, layout):
        """Add threshold controls to the layout."""
        self._add_section_header(layout, "Thresholds")
        self._create_slider_group(layout, "X Min", 0, -15, 15, self.thresholds, 0, 0.1)
        self._create_slider_group(layout, "X Max", 1, -15, 15, self.thresholds, 1, 0.1)
        self._create_slider_group(layout, "Y Min", 2, -10, 50, self.thresholds, 2, 0.1)
        self._create_slider_group(layout, "Y Max", 3, -10, 50, self.thresholds, 3, 0.1)
        self._create_slider_group(layout, "Z Min", 4, -15, 0, self.thresholds, 4, 0.1)
        self._create_slider_group(layout, "Z Max", 5, -10, 0, self.thresholds, 5, 0.1)

    def _add_divider_controls(self, layout):
        """Add divider controls to the layout."""
        self._add_section_header(layout, "Divider Settings")
        self._create_slider_group(layout, "Camera Z", 0, -15, 15, self.divider, 0, 0.1)
        self._create_slider_group(layout, "Top Y Divider", 1, -5, 15, self.divider, 1, 0.01)
        self._create_slider_group(layout, "Bottom Y Divider", 2, -5, 15, self.divider, 2, 0.01)
        self._create_slider_group(layout, "X Divider Angle", 3, 0, 360, self.divider, 3, 1)
        self._create_slider_group(layout, "Top Y Divider Angle", 4, -90, 90, self.divider, 4, 0.1)
        self._create_slider_group(layout, "Bottom Y Divider Angle", 5, -90, 90, self.divider, 5, 0.1)
        
        draw_planes_checkbox = QCheckBox("Draw Planes")
        draw_planes_checkbox.setChecked(self.divider[6])
        draw_planes_checkbox.stateChanged.connect(
            lambda state: setattr(self.live_config, 'draw_planes', bool(state))
        )
        layout.addWidget(draw_planes_checkbox)

    def _add_movement_controls(self, layout):
        """Add movement detection controls to the layout."""
        self._add_section_header(layout, "Movement Detection/Tracking")
        self._create_slider_group(layout, "Min Contour Area", 0, 100, 1000, self.movement, 0, 1)
        self._create_slider_group(layout, "Movement Threshold", 1, 1, 20, self.movement, 1, 1)
        self._create_slider_group(layout, "Headpoint Smoothing", 2, 0, 1, self.movement, 2, 0.1)
        self._create_slider_group(layout, "Active Object Stick Time", 3, 0, 5, self.movement, 3, 1)
        self._create_slider_group(layout, "Conf Thres", 4, 0, 1, self.movement, 4, 0.1)
        self._create_slider_group(layout, "Stationary Timeout", 5, 0, 40, self.movement, 5, 1)
        self._create_slider_group(layout, "ROI Filter Dur", 6, 0, 20, self.movement, 6, 1)

    def _add_smoothing_controls(self, layout):
        """Add smoothing controls to the layout."""
        self._add_section_header(layout, "Smoothing")
        self._create_slider_group(layout, "X Thres", 0, 0, 100, self.smoothing, 0, 1)
        self._create_slider_group(layout, "Y Thres", 1, 0, 100, self.smoothing, 1, 1)

    def _add_point_cloud_controls(self, layout):
        """Add point cloud controls to the layout."""
        self._add_section_header(layout, "Point Cloud Settings")
        self._create_slider_group(layout, "Point Size", 0, 1, 10, self.point_size, 0, 1)
        
        self._add_section_header(layout, "Grid Settings")
        self._create_slider_group(layout, "Num Divisions", 0, 10, 200, self.num_divisions, 0, 10)

    def _add_detection_controls(self, layout):
        """Add detection type controls to the layout."""
        self._add_section_header(layout, "Detection Type")
        
        people_check = QCheckBox("Detect Yolo Objects")
        people_check.setChecked(self.detection_type[0])
        people_check.stateChanged.connect(
            lambda state: setattr(self.live_config, 'detect_people', bool(state))
        )
        layout.addWidget(people_check)
        
        objects_check = QCheckBox("Detect Other Objects")
        objects_check.setChecked(self.detection_type[1])
        objects_check.stateChanged.connect(
            lambda state: setattr(self.live_config, 'detect_objects', bool(state))
        )
        layout.addWidget(objects_check)

    def _add_action_buttons(self, layout):
        """Add action buttons to the layout."""
        edit_cubes_button = QPushButton("Edit Cubes")
        edit_cubes_button.clicked.connect(self.open_edit_cubes_dialog)
        layout.addWidget(edit_cubes_button)

        save_cube_button = QPushButton("Save Cubes")
        save_cube_button.clicked.connect(self.cube_manager.save_cubes)
        layout.addWidget(save_cube_button)

        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

    def _calculate_scaled_values(self, min_val, max_val, current_value, step):
        """Calculate scaled values for slider range and current position.
        
        @return: Tuple of (scaled_min, scaled_max, scaled_value)
        """
        if step < 1:
            scale_factor = 1 if step == 0.1 else 100 if step == 0.01 else 1
            return (
                int(min_val * scale_factor),
                int(max_val * scale_factor),
                int(current_value * scale_factor)
            )
        return min_val, max_val, current_value

    def _update_parameter(self, index, target_list, value, step):
        """Update parameter value and live config.
        
        @param index: Parameter index in target list
        @param target_list: Target parameter list to modify
        @param value: Raw slider value
        @param step: Value scaling factor
        """
        scaled_value = value / (10 if step == 0.1 else 100 if step == 0.01 else 1)
        target_list[index] = scaled_value
        self.sync_with_live_config()

    def _update_value_display(self, label, input_field, value, step):
        """Update displayed value in label and input field.
        
        @param label: QLabel to update
        @param input_field: QLineEdit to update
        @param value: Raw slider value
        @param step: Value scaling factor
        """
        scaled_value = value / (10 if step == 0.1 else 100 if step == 0.01 else 1)
        display_value = f"{scaled_value:.2f}" if step < 1 else f"{int(scaled_value)}"
        label.setText(display_value)
        input_field.setText(display_value)

    def _update_slider_from_input(self, input_field, slider, min_val, max_val, step):
        """Update slider position from input field value."""
        try:
            input_value = float(input_field.text())
            # clamped_value = max(min(input_value, max_val), min_val)
            scaled_value = int(input_value * (10 if step == 0.1 else 100 if step == 0.01 else 1))
            slider.setValue(scaled_value)
        except ValueError:
            pass

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
        """Synchronize UI parameters with live configuration."""
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
        self.live_config.x_divider_angle = self.divider[3]
        self.live_config.y_top_divider_angle = self.divider[4]
        self.live_config.y_bottom_divider_angle = self.divider[5]
        self.live_config.draw_planes = self.divider[6]

        self.live_config.min_contour_area = self.movement[0]
        self.live_config.movement_thres = self.movement[1]
        self.live_config.headpoint_smoothing = self.movement[2]
        self.live_config.active_object_stick_time = self.movement[3]
        self.live_config.conf_thres = self.movement[4]
        self.live_config.stationary_timeout = self.movement[5]
        self.live_config.roi_filter_dur = self.movement[6]
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
        self.live_config.detect_people = self.detection_type[0]
        self.live_config.detect_objects = self.detection_type[1]

    def update_value(self, index, target_list, value, step):
        """
        Update live config dynamically when a slider changes.
        
        @param index: Index for the target parameter
        @param target_list: List containing the target value
        @param value: New value to set
        @param step: Step size for value changes
        """
        # Store the actual value directly - no need for scaling since it's already handled
        target_list[index] = value
                
        # Update live config based on which parameter changed
        if target_list == self.rotation:
            setattr(self.live_config, ["rotate_x", "rotate_y", "rotate_z"][index], value)
        elif target_list == self.translation:
            setattr(self.live_config, ["translate_x", "translate_y", "translate_z"][index], value)
        elif target_list == self.divider:
            setattr(self.live_config, [
                "camera_z", "y_top_divider", "y_bottom_divider",
                "x_divider_angle", "y_top_divider_angle", "y_bottom_divider_angle"
            ][index], value)
        elif target_list == self.movement:
            setattr(self.live_config, [
                "min_contour_area", "movement_thres", "headpoint_smoothing",
                "active_object_stick_time", "conf_thres", "stationary_timeout", "roi_filter_dur"
            ][index], value)
        elif target_list == self.smoothing:
            setattr(self.live_config, ["stable_x_thres", "stable_y_thres"][index], value)
        elif target_list == self.thresholds:
            setattr(self.live_config, [
                "x_threshold_min", "x_threshold_max", "y_threshold_min",
                "y_threshold_max", "z_threshold_min", "z_threshold_max"
            ][index], value)
        elif target_list == self.detection_type:
            setattr(self.live_config, ["detect_people", "detect_objects"][index], value)
        elif target_list == self.point_size:
            self.live_config.point_size = value
        elif target_list == self.num_divisions:
            self.live_config.num_divisions = value