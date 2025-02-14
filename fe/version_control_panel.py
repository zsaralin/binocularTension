from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QEvent

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
        
        # Set window properties
        self.setWindowTitle("Binocular Tension v1.00 - User GUI")
        
        # Install event filter to capture key events
        self.installEventFilter(self)
        
        self.init_ui()

    def eventFilter(self, obj, event):
        """
        Filter events to handle key presses even when panel has focus.
        
        This method intercepts key events and forwards relevant ones to the
        main display window, allowing keyboard shortcuts to work even when
        the panel is focused.
        
        Args:
            obj: The object that triggered the event
            event: The event that was triggered
            
        Returns:
            bool: True if event was handled, False to continue normal event processing
        """
        if event.type() == QEvent.KeyPress:
            # Forward 'c' key press to main display
            if event.key() == Qt.Key_U:
                self.main_display.keyPressEvent(event)
                return True
            # Forward bracket keys for version switching
            elif event.key() in [Qt.Key_BracketLeft, Qt.Key_BracketRight]:
                self.main_display.keyPressEvent(event)
                return True
                
        # Continue normal event processing for other events
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

        nervous_button = QPushButton("Nervous")
        nervous_button.clicked.connect(lambda: self.apply_preset("nervous"))

        stable_button = QPushButton("Stable")
        stable_button.clicked.connect(lambda: self.apply_preset("stable"))

        calm_button = QPushButton("Calm")
        calm_button.clicked.connect(lambda: self.apply_preset("calm"))

        preset_layout.addWidget(nervous_button)
        preset_layout.addWidget(stable_button)
        preset_layout.addWidget(calm_button)
        
        layout.addLayout(preset_layout)
        self.setLayout(layout)

    def apply_preset(self, preset_name: str):
        # print(f"Applying preset: {preset_name}")
        with PresetManager() as pm:
            preset_data = pm.load_preset(f"presets/{preset_name}.json")
            if preset_data:
                # pm.print_preset(preset_data)
                pm.apply_preset(preset_data)

    def closeEvent(self, event):
        """
        Handle the panel close event.
        
        Ensures proper cleanup when the panel is closed:
        - Saves current configuration
        - Clears panel reference in main display
        - Updates cursor visibility
        - Ensures main display regains focus
        
        Args:
            event: The close event object
        """
        self.version_selector.save_config()
        self.main_display.version_panel = None
        self.main_display.setCursor(Qt.BlankCursor)
        self.main_display.activateWindow()
        event.accept()