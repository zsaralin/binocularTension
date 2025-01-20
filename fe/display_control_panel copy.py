import json
import os
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QSlider, QLineEdit, QHBoxLayout, QWidget, QPushButton, QCheckBox, QSpinBox, QComboBox, QRadioButton, QButtonGroup, QDoubleSpinBox
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
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

        self.switch_timer = QTimer()
        self.switch_timer.timeout.connect(self.toggle_folder)
        self.current_auto_switch_interval = 0.0  # Store the interval in seconds


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
        self.stretch_x = [self.config.get("stretch_x", 1)]  # Default 5 seconds
        self.stretch_y = [self.config.get("stretch_y", 1)]  # Default 5 seconds
        self.smooth_y = [self.config.get("smooth_y", 0)]  # Default 5 seconds
        self.rotate = [self.config.get("rotate", 0)]  # Default 5 seconds

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

    def toggle_folder(self):
        """
        Toggle between Jade and Gab folders.
        Called by the timer when auto-switching is enabled.
        """
        if self.main_display.current_folder == "jade":
            self.main_display.switch_image_folder("gab")
            # Update radio button without triggering its toggle handler
            self.gab_radio.blockSignals(True)
            if not self.switch_radio.isChecked():
                self.gab_radio.setChecked(True)
            self.gab_radio.blockSignals(False)
        else:
            self.main_display.switch_image_folder("jade")
            # Update radio button without triggering its toggle handler
            self.jade_radio.blockSignals(True)
            if not self.switch_radio.isChecked():
                self.jade_radio.setChecked(True)
            self.jade_radio.blockSignals(False)

    def update_version_selection(self, folder_name):
        """
        Update the radio button selection to match the current folder.
        
        Args:
            folder_name (str): Name of the selected folder ('jade' or 'gab')
        """
        if folder_name.lower() == 'jade':
            self.jade_radio.setChecked(True)
        elif folder_name.lower() == 'gab':
            self.gab_radio.setChecked(True) 


    def closeEvent(self, event):
        """
        Handle the control panel being closed.
        Make sure to stop the timer when closing.
        """
        # self.switch_timer.stop()
        self.main_display.control_panel = None
        self.main_display.setCursor(Qt.BlankCursor)
        self.main_display.activateWindow()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """
        Handle key events in the control panel.
        Forward relevant keys to the main display.
        """
        if event.key() in [Qt.Key_BracketLeft, Qt.Key_BracketRight, Qt.Key_G]:
            # Forward these keys to the main display
            self.main_display.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def load_config(self):
        if os.path.exists('display_config.json'):
            with open('display_config.json', 'r') as config_file:
                return json.load(config_file)
        return {
            "min_blink_interval": 3,
            "max_blink_interval": 8,
            "min_sleep_timeout": 60,
            "max_sleep_timeout": 180,
            "min_random_wakeup": 30,
            "max_random_wakeup": 60,
            "blink_speed": 5,
            "jitter_start_delay": 0.5,
            "large_jitter_start_delay": 60,
            "min_jitter_interval": 3,
            "max_jitter_interval": 6,
            "min_jitter_speed": 500,
            "max_jitter_speed": 800,
            "display_off_timeout": 1,
            "stretch_x": 1.0,
            "stretch_y": 1.0,
            "smooth_y": 10,
            "rotate": 0,
            "nervousness": 0.8,
            "selected_folder": "jade",  # New: default folder selection
            "auto_switch_enabled": False,  # New: whether auto-switch is enabled
            "auto_switch_interval": 0.5  # New: default interval in minutes
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
            "rotate": self.rotate[0],
            "smooth_y": self.smooth_y[0],
            "nervousness": self.nervousness[0],
            "selected_folder": self.main_display.current_folder,
            "auto_switch_enabled": self.switch_radio.isChecked(),
            "auto_switch_interval": self.current_auto_switch_interval
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
        self.live_config.smooth_y = self.smooth_y[0]
        self.live_config.rotate = self.rotate[0]

    def update_checkbox_state(self, checkbox_name, state):
        self.checkbox_states[checkbox_name] = bool(state)

    def add_version_selection(self, layout):
        """
        Add version selection radio buttons to the control panel.
        Now includes auto-switch option with timer.
        """
        # Add version selection header with keyboard shortcut info
        version_label = QLabel("Version Selection ([ ] keys)")
        version_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(version_label)

        # Create horizontal layout for radio buttons
        version_layout = QHBoxLayout()

        # Create radio buttons with keyboard shortcut hints
        self.jade_radio = QRadioButton("Jade [")
        self.gab_radio = QRadioButton("Gab ]")
        self.switch_radio = QRadioButton("Auto Switch")
        
        # Add radio buttons to horizontal layout
        version_layout.addWidget(self.jade_radio)
        version_layout.addWidget(self.gab_radio)
        version_layout.addWidget(self.switch_radio)

        # Create button group for mutual exclusivity
        self.version_button_group = QButtonGroup(self)
        self.version_button_group.addButton(self.jade_radio)
        self.version_button_group.addButton(self.gab_radio)
        self.version_button_group.addButton(self.switch_radio)

        # Create timer length input widget
        timer_widget = QWidget()
        timer_layout = QHBoxLayout(timer_widget)
        timer_label = QLabel("Switch Interval (minutes):")
        self.timer_spinbox = QDoubleSpinBox()
        self.timer_spinbox.setValue(self.config.get("auto_switch_interval", 0.5))
        self.timer_spinbox.setValue(0.5)  # Default to 30 seconds
        self.timer_spinbox.setSingleStep(0.1)  # Allow fine-grained control
        self.timer_spinbox.setDecimals(2)  # Show 2 decimal places
        self.timer_spinbox.valueChanged.connect(self.update_switch_interval)

        # Load saved interval from config
        saved_interval = self.config.get("auto_switch_interval", 0.5)
        self.timer_spinbox.setValue(saved_interval)

        self.timer_spinbox.setSingleStep(0.1)
        self.timer_spinbox.setDecimals(2)
        
        timer_layout.addWidget(timer_label)
        timer_layout.addWidget(self.timer_spinbox)

        # Connect radio buttons to switching logic
        def on_manual_radio_toggle():
            if self.switch_radio.isChecked():
                return  # Don't do anything if we're in auto-switch mode
            
            if self.jade_radio.isChecked():
                self.main_display.switch_image_folder("jade")
            elif self.gab_radio.isChecked():
                self.main_display.switch_image_folder("gab")

            self.switch_timer.stop()
            self.switch_radio.setChecked(False)
            # save config without auto-switch off
            self.config["auto_switch_enabled"] = False
            self.save_config()
            print("Manual folder selection saved.")
            

        def on_switch_radio_toggle(checked):
            timer_widget.setVisible(checked)
            if checked:
                interval = self.timer_spinbox.value() * 60 * 1000  # Convert to milliseconds
                self.switch_timer.setInterval(int(interval))
                self.switch_timer.start()
            else:
                self.switch_timer.stop()

        # Connect signal handlers
        self.jade_radio.toggled.connect(on_manual_radio_toggle)
        self.gab_radio.toggled.connect(on_manual_radio_toggle)
        self.switch_radio.toggled.connect(on_switch_radio_toggle)
        self.timer_spinbox.valueChanged.connect(lambda value: 
            self.update_switch_interval(value) if self.switch_radio.isChecked() else None)
        
        # Set initial states from config
        auto_switch_enabled = self.config.get("auto_switch_enabled", False)
        timer_widget.setVisible(auto_switch_enabled)
        
        if auto_switch_enabled:
            self.switch_radio.setChecked(True)
            # Start auto-switching with saved interval
            interval = saved_interval * 60 * 1000
            # self.switch_timer.setInterval(int(interval))
            # self.switch_timer.start()
            on_switch_radio_toggle(True)
        else:
            # Only set folder selection if not auto-switching
            selected_folder = self.config.get("selected_folder", "jade")
            if selected_folder == "jade":
                self.jade_radio.setChecked(True)
                self.config["selected_folder"] = "jade"
            else:
                self.gab_radio.setChecked(True)
                self.config["selected_folder"] = "gab"
            self.config["auto_switch_enabled"] = False
            self.save_config()

        layout.addLayout(version_layout)
        layout.addWidget(timer_widget)

    def handle_radio_toggle(self, folder, checked):
        """Handle regular folder radio button toggles."""
        if checked and not self.switch_radio.isChecked():
            self.switch_timer.stop()  # Stop auto-switching if enabled
            self.main_display.switch_image_folder(folder)

    def handle_switch_radio_toggle(self, checked, timer_widget):
        """Handle auto-switch radio button toggle."""
        timer_widget.setVisible(checked)
        if checked:
            self.update_switch_interval(self.timer_spinbox.value())
        else:
            self.switch_timer.stop()

    def update_switch_interval(self, value):
        """Update the auto-switch timer interval."""
        if self.switch_radio.isChecked():
            # Convert minutes to milliseconds
            interval_ms = int(value * 60 * 1000)
            self.switch_timer.stop()
            self.switch_timer.setInterval(interval_ms)
            self.switch_timer.start()
            self.current_auto_switch_interval = value


    def init_ui(self):
        main_layout = QVBoxLayout(self)

        self.add_version_selection(main_layout)

        main_layout.addSpacing(10)

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

        self.create_slider_group(main_layout, "Smooth Y", self.smooth_y, 0, 100, 1)
        self.create_slider_group(main_layout, "Rotate", self.rotate, -5, 5, 0.1)

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
        elif target_list is self.smooth_y:
            self.live_config.smooth_y = value
        elif target_list is self.rotate:
            self.live_config.rotate = value
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
        self.live_config.rotate = self.rotate[0]  
        self.live_config.smooth_y = self.smooth_y[0]  
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