from PyQt5.QtCore import QTimer
import random
import json

class VersionSelector:
    """
    Manages version selection and auto-switching functionality.
    """

    def __init__(self, main_display):
        """
        Initialize the version selector.
        @param main_display: The main display window object.
        @type main_display: QWidget
        """
        self.main_display = main_display
        self.current_folder = "female"  # Default starting folder

        # Shared timer for auto-switching
        if not hasattr(VersionSelector, "_active_timer"):
            VersionSelector._active_timer = QTimer()
        self.switch_timer = VersionSelector._active_timer
        self.switch_timer.timeout.connect(self.toggle_version)

        self.auto_switch_enabled = False  # Internal state
        self.auto_switch_interval_low = 0.5  # Default low end of interval in minutes
        self.auto_switch_interval_high = 0.5  # Default high end of interval in minutes

        # UI elements (set up during setup_ui; reset on close)
        self.female_radio = None
        self.male_radio = None
        self.switch_radio = None
        self.timer_spinbox1 = None
        self.timer_spinbox2 = None

        self.load_config()

    def setup_ui(self, layout):
        """
        This method initializes and configures the UI elements for version selection,
        including radio buttons for selecting between "Female", "Male", and "Auto Switch"
        modes, as well as spin boxes for setting the auto-switch interval.
        @param layout: The main layout to which the UI components will be added.
        @type layout: QVBoxLayout
        """
        from PyQt5.QtWidgets import QLabel, QHBoxLayout, QRadioButton, QButtonGroup, QDoubleSpinBox, QVBoxLayout

        # Version selection header
        version_label = QLabel("Version Selection ([ ] keys)")
        version_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(version_label)

        # Radio button layout
        version_layout = QHBoxLayout()

        # Create and configure radio buttons
        self.female_radio = QRadioButton("Female [")
        self.male_radio = QRadioButton("Male ]")
        self.switch_radio = QRadioButton("Auto Switch")

        self.load_config()
        if self.auto_switch_enabled:
            self.switch_radio.setChecked(True)
        elif self.current_folder == "female":
            self.female_radio.setChecked(True)
        else:
            self.male_radio.setChecked(True)

        # Add buttons to the layout
        version_layout.addWidget(self.female_radio)
        version_layout.addWidget(self.male_radio)
        version_layout.addWidget(self.switch_radio)

        # Button group for mutual exclusivity
        button_group = QButtonGroup()
        button_group.addButton(self.female_radio)
        button_group.addButton(self.male_radio)
        button_group.addButton(self.switch_radio)

        # Add version layout to main layout
        layout.addLayout(version_layout)

        # Timer settings layout
        timer_layout = QHBoxLayout()
        timer_label1 = QLabel("Switch eyes between")
        timer_label2 = QLabel("and")
        timer_label3 = QLabel("minutes")

        self.timer_spinbox1 = QDoubleSpinBox()
        self.timer_spinbox1.setRange(0.1, 1440.0)
        self.timer_spinbox1.setValue(self.auto_switch_interval_low)
        self.timer_spinbox1.setSingleStep(0.1)
        self.timer_spinbox1.setDecimals(2)
        self.timer_spinbox1.valueChanged.connect(self.update_switch_interval_low)

        self.timer_spinbox2 = QDoubleSpinBox()
        self.timer_spinbox2.setRange(0.1, 1440.0)
        self.timer_spinbox2.setValue(self.auto_switch_interval_high)
        self.timer_spinbox2.setSingleStep(0.1)
        self.timer_spinbox2.setDecimals(2)
        self.timer_spinbox2.valueChanged.connect(self.update_switch_interval_high)

        # Add label and spinbox to the timer layout
        timer_layout.addWidget(timer_label1)
        timer_layout.addWidget(self.timer_spinbox1)
        timer_layout.addWidget(timer_label2)
        timer_layout.addWidget(self.timer_spinbox2)
        timer_layout.addWidget(timer_label3)

        # Add timer layout to main layout
        layout.addLayout(timer_layout)

        # Connect UI signals to actions
        self.female_radio.toggled.connect(self.handle_manual_selection)
        self.male_radio.toggled.connect(self.handle_manual_selection)
        self.switch_radio.toggled.connect(self.handle_auto_switch)

    def handle_manual_selection(self):
        """
        Handles when the user selects Female or Male manually.
        """
        if self.switch_radio and self.switch_radio.isChecked():
            return  # Ignore if auto-switch is enabled

        self.stop_auto_switch()

        if self.female_radio and self.female_radio.isChecked():
            self.switch_folder("female")
        elif self.male_radio and self.male_radio.isChecked():
            self.switch_folder("male")

        self.save_config()

    def handle_auto_switch(self, checked):
        """
        Handles when the user enables/disables auto-switching.
        @param checked: Whether the auto-switch radio button is checked.
        @type checked: bool
        """
        self.auto_switch_enabled = checked

        if checked:
            self.start_auto_switch()
        else:
            self.stop_auto_switch()

    def start_auto_switch(self):
        """
        Starts auto-switching with a random value of the current interval.
        """
        self.stop_auto_switch() # Stop any existing timer to ensure only one is running
        interval_min = self.auto_switch_interval_low
        interval_max = self.auto_switch_interval_high
        interval_ms = int(random.uniform(interval_min, interval_max) * 60 * 1000)
        self.switch_timer.setInterval(interval_ms)
        self.switch_timer.start()
        self.auto_switch_enabled = True
        self.save_config()

    def stop_auto_switch(self):
        """
        Stops auto-switching.
        """
        self.switch_timer.stop()
        self.auto_switch_enabled = False
        self.save_config()

    def toggle_version(self):
        """
        Toggles between Female and Male versions.
        Called by the auto-switch timer.
        """
        # Do not rely on UI elements like self.switch_radio here
        if not self.auto_switch_enabled:
            return

        if self.current_folder == "female":
            self.switch_folder("male")
        else:
            self.switch_folder("female")

        self.start_auto_switch()

    def switch_folder(self, folder_name):
        """
        Switch to the specified folder (Female or Male).
        @param folder_name: The name of the folder to switch to.
        @type folder_name: str
        """
        self.current_folder = folder_name
        self.main_display.switch_image_folder(folder_name)
        self.save_config()

    def update_switch_interval_low(self, value):
        """
        Updates the low value for auto-switch interval (in minutes).
        @param value: The new low value for the interval.
        @type value: float
        """
        self.auto_switch_interval_low = min(value, self.auto_switch_interval_high)
        if self.auto_switch_enabled:
            self.start_auto_switch()

    def update_switch_interval_high(self, value):
        """
        Updates the high value for auto-switch interval (in minutes).
        @param value: The new high value for the interval.
        @type value: float
        """
        self.auto_switch_interval_high = max(value, self.auto_switch_interval_low)
        if self.auto_switch_enabled:
            self.start_auto_switch()

    def load_state_from_dict(self, config):
        """
        Loads the saved configuration state.
        @param config: The configuration state to load.
        @type config: dict
        """
        self.auto_switch_enabled = config.get("auto_switch_enabled", False)
        self.auto_switch_interval_low = config.get("auto_switch_interval_low", 0.5)
        self.auto_switch_interval_high = config.get("auto_switch_interval_high", 0.5)
        self.current_folder = config.get("selected_folder", "female")

        if self.auto_switch_enabled:
            self.start_auto_switch()
        else:
            self.switch_folder(self.current_folder)

    def save_state_to_dict(self):
        """
        Returns the current configuration state.
        """
        return {
            "selected_folder": self.current_folder,
            "auto_switch_enabled": self.auto_switch_enabled,
            "auto_switch_interval_low": self.auto_switch_interval_low,
            "auto_switch_interval_high": self.auto_switch_interval_high,
        }

    def save_config(self):
        """Save version selection config to file."""
        config_data = self.save_state_to_dict()
        
        # Merge with existing config if present
        try:
            with open('display_config.json', 'r') as f:
                existing_config = json.load(f)
                existing_config.update(config_data)
                config_data = existing_config
        except (FileNotFoundError, json.JSONDecodeError):
            pass
            
        with open('display_config.json', 'w') as f:
            json.dump(config_data, f, indent=4)

    def load_config(self):
        """Load version selection config from file."""
        try:
            with open('display_config.json', 'r') as f:
                config = json.load(f)
                self.load_state_from_dict(config)
        except (FileNotFoundError, json.JSONDecodeError):
            pass