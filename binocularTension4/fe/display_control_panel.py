import json
import os
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QSlider, QLineEdit, QHBoxLayout, QWidget, QPushButton, QCheckBox, QSpinBox, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal
from display_live_config import DisplayLiveConfig  # Ensure LiveConfig is available

import json
import os
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal
class DisplayControlPanelWidget(QWidget):
    min_blink_interval_changed = pyqtSignal(int)
    max_blink_interval_changed = pyqtSignal(int)
    min_sleep_timeout_changed = pyqtSignal(int)
    max_sleep_timeout_changed = pyqtSignal(int)
    min_random_wakeup_changed = pyqtSignal(int)  # New signal for min random wakeup
    max_random_wakeup_changed = pyqtSignal(int)  # New signal for max random wakeup
    display_off_timeout_changed = pyqtSignal(int)  # New signal for display off timeout

    def __init__(self, display, main_display, parent=None):  # Add display parameter
        super(DisplayControlPanelWidget, self).__init__(parent)
        self.display = display
        self.config = self.load_config()
        self.live_config = DisplayLiveConfig.get_instance()  # Access LiveConfig singleton instance
        self.main_display = main_display

        # Initialize target lists with single elements for each setting
        self.min_blink_interval = [self.config.get("min_blink_interval", 3000)]
        self.max_blink_interval = [self.config.get("max_blink_interval", 6000)]
        self.min_sleep_timeout = [self.config.get("min_sleep_timeout", 60)]  # Default 1 minute
        self.max_sleep_timeout = [self.config.get("max_sleep_timeout", 180)]  # Default 3 minutes
        self.min_random_wakeup = [self.config.get("min_random_wakeup", 60)]  # Default 1 minute
        self.max_random_wakeup = [self.config.get("max_random_wakeup", 180)]  # Default 3 minutes
        self.blink_speed = [self.config.get("blink_speed", 5)]
        self.jitter_start_delay = [self.config.get("jitter_start_delay", 120)]
        self.large_jitter_start_delay = [self.config.get("large_jitter_start_delay", 300)]  # Default 5 minutes
        self.min_jitter_interval = [self.config.get("min_jitter_interval", 3000)]
        self.max_jitter_interval = [self.config.get("max_jitter_interval", 6000)]
        self.min_jitter_speed = [self.config.get("min_jitter_speed", 1)]  # Default minimum speed
        self.max_jitter_speed = [self.config.get("max_jitter_speed", 10)]  # Default maximum speed
        self.display_off_timeout = [self.config.get("display_off_timeout", 5)]  # Default 5 seconds
        self.stretch_x = [self.config.get("stretch_x", 0)]  # Default 5 seconds
        self.stretch_y = [self.config.get("stretch_y", 0)]  # Default 5 seconds
        self.nervousness = [self.config.get("nervousness", 0)]  # Default 5 seconds

        # Initialize checkbox states
        self.checkbox_states = {
            "debug": False,
            "open": False,
            "closed": False,
            "half": False,
            "surprised": False
        }

        # Initialize the UI and sliders
        self.init_ui()
        self.sync_with_live_config()  # Update LiveConfig with initial values

    def closeEvent(self, event):
        """Handle the close event to hide the cursor on the main display."""
        self.main_display.setCursor(Qt.BlankCursor)  # Hide the cursor on close
        super().closeEvent(event)

    def load_config(self):
        if os.path.exists('display_config.json'):
            with open('display_config.json', 'r') as config_file:
                return json.load(config_file)
        else:
            return {
                "min_blink_interval": 180,
                "max_blink_interval": 360,
                "min_sleep_timeout": 60,
                "max_sleep_timeout": 180,
                "min_random_wakeup": 60,
                "max_random_wakeup": 180,
                "blink_speed": 5,
                "jitter_start_delay": 120,
                "large_jitter_start_delay": 300,
                "min_jitter_interval": 180,
                "max_jitter_interval": 360,
                "min_jitter_speed": 1,
                "max_jitter_speed": 10,
                "display_off_timeout": 5,
                "stretch_x": 0,
                "stretch_y": 0,
                "nervousness": 0
            }

    def save_config(self):
        config_data = {
            "min_blink_interval": self.min_blink_interval[0],
            "max_blink_interval": self.max_blink_interval[0],
            "min_sleep_timeout": self.min_sleep_timeout[0],
            "max_sleep_timeout": self.max_sleep_timeout[0],
            "min_random_wakeup": self.min_random_wakeup[0],
            "max_random_wakeup": self.max_random_wakeup[0],
            "blink_speed": self.blink_speed[0],
            "jitter_start_delay": self.jitter_start_delay[0],
            "large_jitter_start_delay": self.large_jitter_start_delay[0],
            "min_jitter_interval": self.min_jitter_interval[0],
            "max_jitter_interval": self.max_jitter_interval[0],
            "min_jitter_speed": self.min_jitter_speed[0],
            "max_jitter_speed": self.max_jitter_speed[0],
            "display_off_timeout": self.display_off_timeout[0],
            "stretch_x": self.stretch_x[0],
            "stretch_y": self.stretch_y[0],
            "nervousness": self.nervousness[0]
        }
        with open('display_config.json', 'w') as config_file:
            json.dump(config_data, config_file, indent=4)
        print("Configuration saved to display_config.json")

    def sync_with_live_config(self):
        """Updates the live configuration with current values."""
        self.live_config.min_blink_interval = self.min_blink_interval[0]
        self.live_config.max_blink_interval = self.max_blink_interval[0]
        self.live_config.min_sleep_timeout = self.min_sleep_timeout[0]
        self.live_config.max_sleep_timeout = self.max_sleep_timeout[0]
        self.live_config.min_random_wakeup = self.min_random_wakeup[0]
        self.live_config.max_random_wakeup = self.max_random_wakeup[0]
        self.live_config.blink_speed = self.blink_speed[0]
        self.live_config.jitter_start_delay = self.jitter_start_delay[0]
        self.live_config.large_jitter_start_delay = self.large_jitter_start_delay[0]
        self.live_config.min_jitter_interval = self.min_jitter_interval[0]
        self.live_config.max_jitter_interval = self.max_jitter_interval[0]
        self.live_config.min_jitter_speed = self.min_jitter_speed[0]
        self.live_config.max_jitter_speed = self.max_jitter_speed[0]
        self.live_config.display_off_timeout = self.display_off_timeout[0]
        self.live_config.stretch_x = self.stretch_x[0]
        self.live_config.stretch_y = self.stretch_y[0]


    def update_checkbox_state(self, checkbox_name, state):
        self.checkbox_states[checkbox_name] = bool(state)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Add min and max blink interval sliders
        self.create_slider_group(main_layout, "Min Blink Interval (s)", self.min_blink_interval, 1, 20, 1)
        self.create_slider_group(main_layout, "Max Blink Interval (s)", self.max_blink_interval, 1, 20, 1)

        # Add sleep timeout sliders
        self.create_slider_group(main_layout, "Min Sleep Timeout (s)", self.min_sleep_timeout, 1, 300, 1)
        self.create_slider_group(main_layout, "Max Sleep Timeout (s)", self.max_sleep_timeout, 1, 300, 1)
        
        # Add random wakeup sliders
        self.create_slider_group(main_layout, "Min Random Wakeup (s)", self.min_random_wakeup, 1, 300, 1)
        self.create_slider_group(main_layout, "Max Random Wakeup (s)", self.max_random_wakeup, 1, 300, 1)

        # Add jitter-related sliders
        self.create_slider_group(main_layout, "Jitter Start Delay (s)", self.jitter_start_delay, 0, 1000, .1)
        self.create_slider_group(main_layout, "Large Jitter Start Delay (s)", self.large_jitter_start_delay, 1, 1000, 1)
        self.create_slider_group(main_layout, "Min Jitter Speed (ms)", self.min_jitter_speed, 100, 1000, 1)
        self.create_slider_group(main_layout, "Max Jitter Speed (ms)", self.max_jitter_speed, 100, 2000, 1)
        self.create_slider_group(main_layout, "Min Jitter Interval (s)", self.min_jitter_interval, 1, 300, 1)
        self.create_slider_group(main_layout, "Max Jitter Interval (s)", self.max_jitter_interval, 1, 300, 1)

        # Add blink speed slider
        self.create_slider_group(main_layout, "Blink Speed", self.blink_speed, 1, 20, 1)

        # Add stretch sliders
        self.create_slider_group(main_layout, "Stretch X", self.stretch_x, 1, 1.5, 0.01)
        self.create_slider_group(main_layout, "Stretch Y", self.stretch_y, 1, 1.5, 0.01)

        # Add nervousness slider
        self.create_slider_group(main_layout, "Nervousness", self.nervousness, 0, 1, 0.1)
        # Add checkboxes
        checkbox_layout = QVBoxLayout()
        self.debug_checkbox = QCheckBox("Debug")
        self.debug_checkbox.stateChanged.connect(self.on_debug_checkbox_changed)
        checkbox_layout.addWidget(self.debug_checkbox)

        # Additional checkboxes for "Open", "Closed", "Half", and "Surprised" modes
        self.open_checkbox = QCheckBox("Open")
        self.open_checkbox.stateChanged.connect(lambda state: self.display.update_display_mode(new_mode='o' if state else None))
        checkbox_layout.addWidget(self.open_checkbox)

        self.closed_checkbox = QCheckBox("Closed")
        self.closed_checkbox.stateChanged.connect(lambda state: self.display.update_display_mode(new_mode='c' if state else None))
        checkbox_layout.addWidget(self.closed_checkbox)

        self.half_checkbox = QCheckBox("Half")
        self.half_checkbox.stateChanged.connect(lambda state: self.display.update_display_mode(new_mode='h' if state else None))
        checkbox_layout.addWidget(self.half_checkbox)

        self.surprised_checkbox = QCheckBox("Surprised")
        self.surprised_checkbox.stateChanged.connect(lambda state: self.display.update_display_mode(new_mode='w' if state else None))
        checkbox_layout.addWidget(self.surprised_checkbox)

        self.open_checkbox.setVisible(False)
        self.closed_checkbox.setVisible(False)
        self.half_checkbox.setVisible(False)
        self.surprised_checkbox.setVisible(False)

        # X Position Spinbox
        self.xpos_widget = QWidget()
        xpos_layout = QHBoxLayout(self.xpos_widget)
        self.xpos_widget.setLayout(xpos_layout)
        self.xpos_label = QLabel("X Position:")
        xpos_layout.addWidget(self.xpos_label)
        self.xpos_spinbox = QSpinBox()
        self.xpos_spinbox.setRange(0, 41)
        self.xpos_spinbox.setValue(0)
        self.xpos_spinbox.valueChanged.connect(lambda value: self.display.update_display_mode(new_xpos=value))
        xpos_layout.addWidget(self.xpos_spinbox)
        self.xpos_widget.setVisible(False)
        checkbox_layout.addWidget(self.xpos_widget)

        # Y Position Dropdown
        self.ypos_widget = QWidget()
        ypos_layout = QVBoxLayout(self.ypos_widget)
        self.ypos_widget.setLayout(ypos_layout)
        self.ypos_label = QLabel("Y Position")
        ypos_layout.addWidget(self.ypos_label)
        self.ypos_dropdown = QComboBox()
        self.ypos_dropdown.addItems(["Up", "Straight", "Down"])
        self.ypos_dropdown.setCurrentText("Straight")
        self.ypos_dropdown.currentTextChanged.connect(lambda text: self.display.update_display_mode(new_ypos={'Up': 'u', 'Straight': 's', 'Down': 'd'}[text]))
        ypos_layout.addWidget(self.ypos_dropdown)
        self.ypos_widget.setVisible(False)
        checkbox_layout.addWidget(self.ypos_widget)

        # Z Position Dropdown
        self.zpos_widget = QWidget()
        zpos_layout = QVBoxLayout(self.zpos_widget)
        self.zpos_widget.setLayout(zpos_layout)
        self.zpos_label = QLabel("Z Position")
        zpos_layout.addWidget(self.zpos_label)
        self.zpos_dropdown = QComboBox()
        self.zpos_dropdown.addItems(["Close", "Far"])
        self.zpos_dropdown.setCurrentText("Close")
        self.zpos_dropdown.currentTextChanged.connect(lambda text: self.display.update_display_mode(new_zpos={'Close': 'c', 'Far': 'f'}[text]))
        zpos_layout.addWidget(self.zpos_dropdown)
        self.zpos_widget.setVisible(False)
        checkbox_layout.addWidget(self.zpos_widget)

        main_layout.addLayout(checkbox_layout)

        # Add Save button
        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        main_layout.addWidget(save_button)

        self.setLayout(main_layout)
    def create_slider_group(self, layout, label_text, target_list, min_val, max_val, step):
        """
        Create a slider group that works with a step of 0.1 and updates the target list.
        """
        hbox = QHBoxLayout()
        
        # Scale values to integers for the slider
        scaled_min = int(min_val / step)
        scaled_max = int(max_val / step)
        scaled_value = int(target_list[0] / step)

        label = QLabel(label_text)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(scaled_min)
        slider.setMaximum(scaled_max)
        slider.setValue(scaled_value)

        value_label = QLabel(f"{target_list[0]:.1f}")
        value_label.setAlignment(Qt.AlignRight)
        input_field = QLineEdit(f"{target_list[0]:.1f}")
        input_field.setFixedWidth(50)
        input_field.setAlignment(Qt.AlignCenter)

        # Connect input and slider interactions
        input_field.returnPressed.connect(
            lambda: self.update_slider_from_input(input_field, slider, min_val, max_val, step)
        )
        slider.valueChanged.connect(
            lambda value: self.update_value_display(value_label, input_field, value * step)
        )
        slider.valueChanged.connect(
            lambda value: self.update_value(target_list, value * step)
        )

        hbox.addWidget(label)
        hbox.addWidget(slider)
        hbox.addWidget(value_label)
        hbox.addWidget(input_field)
        layout.addLayout(hbox)

    def update_value_display(self, label, input_field, value):
        display_value = f"{value}"
        label.setText(display_value)
        input_field.setText(display_value)

    def update_value(self, target_list, value):
        target_list[0] = value  # Access the single element directly

        if target_list is self.min_blink_interval:
            self.live_config.min_blink_interval = value
            self.min_blink_interval_changed.emit(value)
        elif target_list is self.max_blink_interval:
            self.live_config.max_blink_interval = value
            self.max_blink_interval_changed.emit(value)
        elif target_list is self.min_sleep_timeout:
            self.live_config.min_sleep_timeout = value
            self.min_sleep_timeout_changed.emit(value)
        elif target_list is self.max_sleep_timeout:
            self.live_config.max_sleep_timeout = value
            self.max_sleep_timeout_changed.emit(value)
        elif target_list is self.min_random_wakeup:
            self.live_config.min_random_wakeup = value
            self.min_random_wakeup_changed.emit(value)  # Emit signal for min random wakeup
        elif target_list is self.max_random_wakeup:
            self.live_config.max_random_wakeup = value
            self.max_random_wakeup_changed.emit(value)  # Emit signal for max random wakeup
        elif target_list is self.blink_speed:
            self.live_config.blink_speed = value
        elif target_list is self.jitter_start_delay:
            self.live_config.jitter_start_delay = value
        elif target_list is self.min_jitter_interval:
            self.live_config.min_jitter_interval = value
        elif target_list is self.max_jitter_interval:
            self.live_config.max_jitter_interval = value
        elif target_list is self.display_off_timeout:
            self.live_config.display_off_timeout = value
            self.display_off_timeout_changed.emit(value)
        elif target_list is self.stretch_x:
            self.live_config.stretch_x = value
        elif target_list is self.stretch_y:
            self.live_config.stretch_y = value
        elif target_list is self.nervousness:
            self.live_config.nervousness = value
    def sync_with_live_config(self):
        """Updates the live configuration with current values."""
        self.live_config.min_blink_interval = self.min_blink_interval[0]
        self.live_config.max_blink_interval = self.max_blink_interval[0]
        self.live_config.min_sleep_timeout = self.min_sleep_timeout[0]
        self.live_config.max_sleep_timeout = self.max_sleep_timeout[0]
        self.live_config.min_random_wakeup = self.min_random_wakeup[0]
        self.live_config.max_random_wakeup = self.max_random_wakeup[0]
        self.live_config.blink_speed = self.blink_speed[0]
        self.live_config.display_off_timeout = self.display_off_timeout[0]  
        self.live_config.stretch_x = self.stretch_x[0]  
        self.live_config.stretch_y = self.stretch_y[0]  
        self.live_config.nervousness = self.nervousness[0]  

    def update_slider_from_input(self, input_field, slider, min_val, max_val, step):
        try:
            input_value = int(input_field.text())
            input_value = max(min(input_value, max_val), min_val)
            slider.setValue(input_value)
        except ValueError:
            pass

    def toggle_advanced_checkboxes(self, state):
        """Show or hide advanced checkboxes based on 'Debug' checkbox state and adjust widget height."""
        visible = bool(state)
        for checkbox in self.advanced_checkboxes:
            checkbox.setVisible(visible)
        
        # Adjust widget height based on checkbox visibility
        if visible:
            self.setMinimumHeight(self.sizeHint().height())
            self.setMaximumHeight(self.sizeHint().height())
        else:
            # Adjust back to the original height when checkboxes are hidden
            self.setMinimumHeight(self.sizeHint().height() - len(self.advanced_checkboxes) * 25)
            self.setMaximumHeight(self.sizeHint().height() - len(self.advanced_checkboxes) * 25)

    def on_debug_checkbox_changed(self, state):
        checked = state == Qt.Checked
        self.display.debug_mode = checked
        print(f"Debug mode {'enabled' if checked else 'disabled'}.")

        self.advanced_checkboxes = [
            self.open_checkbox,
            self.closed_checkbox,
            self.half_checkbox,
            self.surprised_checkbox
        ]

        # Show or hide advanced checkboxes based on debug mode
        for checkbox in self.advanced_checkboxes:
            checkbox.setVisible(checked)

        if checked:
            # Parse the current values
            base, xpos, depth, current_ypos, current_mode = self.display.parse_filename()
            print(self.display.parse_filename())
            # Update widget values with parsed values
            self.xpos_spinbox.setValue(int(xpos))  # Set the current xpos
            if current_ypos.lower() == 'u':
                self.ypos_dropdown.setCurrentText("Up")
            elif current_ypos.lower() == 's':
                self.ypos_dropdown.setCurrentText("Straight")
            elif current_ypos.lower() == 'd':
                self.ypos_dropdown.setCurrentText("Down")

            # Convert and set zpos dropdown based on parsed depth value
            if depth.lower() == 'c':
                self.zpos_dropdown.setCurrentText("Close")
            elif depth.lower() == 'f':
                self.zpos_dropdown.setCurrentText("Far")
            # Make widgets visible
            self.xpos_widget.setVisible(True)
            self.ypos_widget.setVisible(True)
            self.zpos_widget.setVisible(True)
        else:
            # Hide widgets if debug mode is unchecked
            self.xpos_widget.setVisible(False)
            self.ypos_widget.setVisible(False)
            self.zpos_widget.setVisible(False)

        # Adjust the widget height based on the visibility of the advanced checkboxes
        if checked:
            self.setMinimumHeight(self.sizeHint().height())
            self.setMaximumHeight(self.sizeHint().height())
        else:
            # Adjust back to the original height when checkboxes are hidden
            height_adjustment = len(self.advanced_checkboxes) * 60
            self.setMinimumHeight(self.sizeHint().height() - height_adjustment)
            self.setMaximumHeight(self.sizeHint().height() - height_adjustment)