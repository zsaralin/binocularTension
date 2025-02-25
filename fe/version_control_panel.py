import socket
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QButtonGroup
from PyQt5.QtCore import Qt, QEvent, QSettings, QTimer
from preset_manager import PresetManager

class VersionControlPanel(QWidget):
    """
    Control panel for version selection and management.
    
    This panel provides UI controls for switching between different versions
    and manages version-related settings. It also handles key event forwarding
    to maintain proper keyboard shortcuts even when the panel has focus.
    """
    
    def __init__(self, main_display, version_selector, parent=None):
        """
        Initialize the version control panel.
        
        Args:
            main_display: Reference to the main display window
            version_selector: Instance of the VersionSelector class
            parent: Parent widget (default: None)
        """
        super().__init__(parent)
        self.main_display = main_display
        self.version_selector = version_selector

        # Persistent settings to remember last selected button
        self.settings = QSettings("MyApp", "VersionControlPanel")

        # Set window properties
        self.setWindowTitle("Binocular Tension v1.02 - User GUI")
        
        # Install event filter to capture key events
        self.installEventFilter(self)
        self.setMinimumWidth(600)

        self.init_ui()
        self.start_camera_status_check()

    def eventFilter(self, obj, event):
        """
        Filter events to handle key presses even when panel has focus.
        """
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_U:
                self.main_display.keyPressEvent(event)
                return True
            elif event.key() in [Qt.Key_Left, Qt.Key_Right]:
                self.main_display.keyPressEvent(event)
                return True
            elif event.key() in [Qt.Key_Down,Qt.Key_Up]:
                self.main_display.keyPressEvent(event)
                return True

                
        return super().eventFilter(obj, event)

    def init_ui(self):
        """Initialize the user interface components."""
        layout = QVBoxLayout()
        # Version selector controls
        self.version_selector.setup_ui(layout)

        # Preset controls
        preset_label = QLabel("Pre Selected Settings")
        preset_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preset_label)
        
        preset_layout = QHBoxLayout()

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)  # Only one button can be checked at a time

        # Create buttons
        self.nervous_button = QPushButton("Nervous")
        self.nervous_button.setCheckable(True)
        self.nervous_button.clicked.connect(lambda: self.apply_preset("nervous"))

        self.stable_button = QPushButton("Stable")
        self.stable_button.setCheckable(True)
        self.stable_button.clicked.connect(lambda: self.apply_preset("stable"))

        self.calm_button = QPushButton("Calm")
        self.calm_button.setCheckable(True)
        self.calm_button.clicked.connect(lambda: self.apply_preset("calm"))
        
        # Add buttons to button group
        self.button_group.addButton(self.nervous_button)
        self.button_group.addButton(self.stable_button)
        self.button_group.addButton(self.calm_button)

        # Add buttons to layout
        preset_layout.addWidget(self.nervous_button)
        preset_layout.addWidget(self.stable_button)
        preset_layout.addWidget(self.calm_button)

        layout.addLayout(preset_layout)

        # Camera Status Display
        self.camera_status_label = QLabel("Camera Status: Checking...")
        self.camera_status_label.setAlignment(Qt.AlignCenter)
        self.camera_status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: gray;")
        layout.addWidget(self.camera_status_label)
        
        self.setLayout(layout)

    def start_camera_status_check(self):
        """Start periodic checks for the camera connection status."""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera_status)
        self.timer.start(1000)  # Check every second

    def update_camera_status(self):
        """Check the camera status from the server and update the UI label."""
        status = self.check_camera_status()
        if status == "connected":
            self.camera_status_label.setText("Camera Connected/Backend Running: ✅")
            # self.camera_status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        else:
            self.camera_status_label.setText("Camera Connected/Backend Running: ❌")
            # self.camera_status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: black;")

    def check_camera_status(self):
        """Query the RealSenseManager server to check camera status."""
        host = "localhost"
        port = 12345

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)  # 1 second timeout
                s.connect((host, port))
                status = s.recv(1024).decode().strip()
                return status
        except Exception:
            return "disconnected"

    def apply_preset(self, preset_name: str):
        """Apply the selected preset and save the selection."""
        with PresetManager() as pm:
            preset_data = pm.load_preset(f"presets/{preset_name}.json")
            if preset_data:
                pm.apply_preset(preset_data)
                if pm.auto_switch_interval_low is not None:
                    self.version_selector.update_switch_interval_low(pm.auto_switch_interval_low)
                    self.version_selector.timer_spinbox1.setValue(pm.auto_switch_interval_low)
                    pm.auto_switch_interval_low = None
                if pm.auto_switch_interval_high is not None:
                    self.version_selector.update_switch_interval_high(pm.auto_switch_interval_high)
                    self.version_selector.timer_spinbox2.setValue(pm.auto_switch_interval_high)
                    pm.auto_switch_interval_high = None

        # Save the selected preset in QSettings
        self.settings.setValue("selected_preset", preset_name)

    def closeEvent(self, event):
        """
        Handle the panel close event.
        """
        self.version_selector.save_config()
        # self.main_display.version_panel = None
        self.main_display.setCursor(Qt.BlankCursor)
        self.main_display.activateWindow()
        self.hide()
        event.ignore()
