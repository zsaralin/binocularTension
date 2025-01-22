from PyQt5.QtCore import QTimer

class VersionSelector:
    """
    Manages version selection and auto-switching functionality.
    """

    def __init__(self, main_display):
        self.main_display = main_display
        self.current_folder = "jade"  # Default starting folder

        # Shared timer for auto-switching
        if not hasattr(VersionSelector, "_active_timer"):
            VersionSelector._active_timer = QTimer()
        self.switch_timer = VersionSelector._active_timer
        self.switch_timer.timeout.connect(self.toggle_version)

        self.auto_switch_enabled = False  # Internal state
        self.auto_switch_interval = 0.5  # Default interval in minutes

        # UI elements (set up during setup_ui; reset on close)
        self.jade_radio = None
        self.gab_radio = None
        self.switch_radio = None
        self.timer_spinbox1 = None
        self.timer_spinbox2 = None

    def setup_ui(self, layout):
        """
        Sets up the version selection UI components in the control panel.
        """
        from PyQt5.QtWidgets import QLabel, QHBoxLayout, QRadioButton, QButtonGroup, QDoubleSpinBox, QVBoxLayout

        # Version selection header
        version_label = QLabel("Version Selection ([ ] keys)")
        version_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(version_label)

        # Radio button layout
        version_layout = QHBoxLayout()

        # Create and configure radio buttons
        self.jade_radio = QRadioButton("Jade [")
        self.gab_radio = QRadioButton("Gab ]")
        self.switch_radio = QRadioButton("Auto Switch")

        # Add buttons to the layout
        version_layout.addWidget(self.jade_radio)
        version_layout.addWidget(self.gab_radio)
        version_layout.addWidget(self.switch_radio)

        # Button group for mutual exclusivity
        button_group = QButtonGroup()
        button_group.addButton(self.jade_radio)
        button_group.addButton(self.gab_radio)
        button_group.addButton(self.switch_radio)

        # Add version layout to main layout
        layout.addLayout(version_layout)

        # Timer settings layout
        timer_layout = QHBoxLayout()
        timer_label1 = QLabel("Switch eyes between")
        timer_label2 = QLabel("and")
        timer_label3 = QLabel("minutes")

        self.timer_spinbox1 = QDoubleSpinBox()
        self.timer_spinbox1.setRange(0.1, 60.0)
        self.timer_spinbox1.setValue(self.auto_switch_interval)
        self.timer_spinbox1.setSingleStep(0.1)
        self.timer_spinbox1.setDecimals(2)
        self.timer_spinbox1.valueChanged.connect(self.update_switch_interval)

        self.timer_spinbox2 = QDoubleSpinBox()
        self.timer_spinbox2.setRange(0.1, 60.0)
        self.timer_spinbox2.setValue(self.auto_switch_interval)
        self.timer_spinbox2.setSingleStep(0.1)
        self.timer_spinbox2.setDecimals(2)

        # Add label and spinbox to the timer layout
        timer_layout.addWidget(timer_label1)
        timer_layout.addWidget(self.timer_spinbox1)
        timer_layout.addWidget(timer_label2)
        timer_layout.addWidget(self.timer_spinbox2)
        timer_layout.addWidget(timer_label3)

        # Add timer layout to main layout
        layout.addLayout(timer_layout)

        # Connect UI signals to actions
        self.jade_radio.toggled.connect(self.handle_manual_selection)
        self.gab_radio.toggled.connect(self.handle_manual_selection)
        self.switch_radio.toggled.connect(self.handle_auto_switch)

    def handle_manual_selection(self):
        """
        Handles when the user selects Jade or Gab manually.
        """
        if self.switch_radio and self.switch_radio.isChecked():
            return  # Ignore if auto-switch is enabled

        self.stop_auto_switch()

        if self.jade_radio and self.jade_radio.isChecked():
            self.switch_folder("jade")
        elif self.gab_radio and self.gab_radio.isChecked():
            self.switch_folder("gab")

    def handle_auto_switch(self, checked):
        """
        Handles when the user enables/disables auto-switching.
        """
        self.auto_switch_enabled = checked

        if checked:
            self.start_auto_switch()
        else:
            self.stop_auto_switch()

    def start_auto_switch(self):
        """
        Starts auto-switching with the current interval.
        """
        interval_ms = int(self.auto_switch_interval * 60 * 1000)
        self.switch_timer.setInterval(interval_ms)
        self.switch_timer.start()
        self.auto_switch_enabled = True

    def stop_auto_switch(self):
        """
        Stops auto-switching.
        """
        self.switch_timer.stop()
        self.auto_switch_enabled = False

    def toggle_version(self):
        """
        Toggles between Jade and Gab versions.
        Called by the auto-switch timer.
        """
        # Do not rely on UI elements like self.switch_radio here
        if not self.auto_switch_enabled:
            return

        if self.current_folder == "jade":
            self.switch_folder("gab")
        else:
            self.switch_folder("jade")

    def switch_folder(self, folder_name):
        """
        Switch to the specified folder (Jade or Gab).
        """
        self.current_folder = folder_name
        self.main_display.switch_image_folder(folder_name)

    def update_switch_interval(self, value):
        """
        Updates the auto-switch interval (in minutes).
        """
        self.auto_switch_interval = value
        if self.auto_switch_enabled:
            self.start_auto_switch()

    def load_state_from_dict(self, config):
        """
        Loads the saved configuration state.
        """
        self.auto_switch_enabled = config.get("auto_switch_enabled", False)
        self.auto_switch_interval = config.get("auto_switch_interval", 0.5)
        self.current_folder = config.get("selected_folder", "jade")

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
            "auto_switch_interval": self.auto_switch_interval,
        }
