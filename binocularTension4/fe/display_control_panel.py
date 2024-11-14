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
    inactivity_timer_changed = pyqtSignal(int)
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
        self.min_sleep_timeout = [self.config.get("min_sleep_timeout", 1)]  # Default 1 minute
        self.max_sleep_timeout = [self.config.get("max_sleep_timeout", 3)]  # Default 3 minutes
        self.min_random_wakeup = [self.config.get("min_random_wakeup", 1)]  # Default 1 minute
        self.max_random_wakeup = [self.config.get("max_random_wakeup", 3)]  # Default 3 minutes
        self.inactivity_timer = [self.config.get("inactivity_timer", 2)]  # Default inactivity timer in minutes
        self.display_off_timeout = [self.config.get("display_off_timeout", 5)]  # Default 5 seconds

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
                "min_blink_interval": 3000,
                "max_blink_interval": 6000,
                "min_sleep_timeout": 1,
                "max_sleep_timeout": 3,
                "min_random_wakeup": 1,
                "max_random_wakeup": 3,
                "inactivity_timer": 2,
                "display_off_timeout": 5

            }

    def save_config(self):
        config_data = {
            "min_blink_interval": self.min_blink_interval[0],
            "max_blink_interval": self.max_blink_interval[0],
            "min_sleep_timeout": self.min_sleep_timeout[0],
            "max_sleep_timeout": self.max_sleep_timeout[0],
            "min_random_wakeup": self.min_random_wakeup[0],
            "max_random_wakeup": self.max_random_wakeup[0],
            "inactivity_timer": self.inactivity_timer[0],
            "display_off_timeout": self.display_off_timeout[0]

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
        self.live_config.inactivity_timer = self.inactivity_timer[0]
        self.live_config.display_off_timeout = self.display_off_timeout[0]


    def update_checkbox_state(self, checkbox_name, state):
        self.checkbox_states[checkbox_name] = bool(state)

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Add min and max blink interval sliders
        self.create_slider_group(main_layout, "Min Blink Interval (ms)", self.min_blink_interval, 1000, 10000, 100)
        self.create_slider_group(main_layout, "Max Blink Interval (ms)", self.max_blink_interval, 1000, 20000, 100)

        # Add sleep timeout slider
        self.create_slider_group(main_layout, "Min Sleep Timeout (s)", self.min_sleep_timeout, 1, 15, 1)
        self.create_slider_group(main_layout, "Max Sleep Timeout (s)", self.max_sleep_timeout, 1, 15, 1)
        
        self.create_slider_group(main_layout, "Min Random Wakeup (s)", self.min_random_wakeup, 1, 15, 1)
        self.create_slider_group(main_layout, "Max Random Wakeup (s)", self.max_random_wakeup, 1, 15, 1)

        # Add inactivity timer slider (1-5 seconds)
        self.create_slider_group(main_layout, "Inactivity Timer (s)", self.inactivity_timer, 1, 5, 1)

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
        hbox = QHBoxLayout()
        scaled_value = target_list[0]

        label = QLabel(label_text)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(scaled_value)
        slider.setSingleStep(step)
        value_label = QLabel(f"{scaled_value}")
        value_label.setAlignment(Qt.AlignRight)
        input_field = QLineEdit(f"{scaled_value}")
        input_field.setFixedWidth(50)
        input_field.setAlignment(Qt.AlignCenter)

        input_field.returnPressed.connect(lambda: self.update_slider_from_input(input_field, slider, min_val, max_val, step))
        slider.valueChanged.connect(lambda value: self.update_value_display(value_label, input_field, value))
        slider.valueChanged.connect(lambda value: self.update_value(target_list, value))

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
        elif target_list is self.inactivity_timer:
            self.live_config.inactivity_timer = value * 1000  # Convert seconds to milliseconds
            self.inactivity_timer_changed.emit(value)
        elif target_list is self.display_off_timeout:
            self.live_config.display_off_timeout = value
            self.display_off_timeout_changed.emit(value)

    def sync_with_live_config(self):
        """Updates the live configuration with current values."""
        self.live_config.min_blink_interval = self.min_blink_interval[0]
        self.live_config.max_blink_interval = self.max_blink_interval[0]
        self.live_config.min_sleep_timeout = self.min_sleep_timeout[0]
        self.live_config.max_sleep_timeout = self.max_sleep_timeout[0]
        self.live_config.min_random_wakeup = self.min_random_wakeup[0]
        self.live_config.max_random_wakeup = self.max_random_wakeup[0]
        self.live_config.inactivity_timer = self.inactivity_timer[0] * 1000  # Convert seconds to milliseconds
        self.live_config.display_off_timeout = self.display_off_timeout[0]  

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