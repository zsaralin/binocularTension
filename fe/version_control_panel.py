from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QEvent

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
            if event.key() == Qt.Key_C:
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

        fair_button = QPushButton("Fair")
        fair_button.clicked.connect(self.set_fair_preset)
        
        home_button = QPushButton("Home")
        home_button.clicked.connect(self.set_home_preset)

        museum_button = QPushButton("Museum")
        museum_button.clicked.connect(self.set_museum_preset)
        
        preset_layout.addWidget(fair_button)
        preset_layout.addWidget(museum_button)
        preset_layout.addWidget(home_button)
        
        layout.addLayout(preset_layout)
        self.setLayout(layout)

    def set_home_preset(self):
        """Apply home environment preset settings."""
        self.version_selector.update_switch_interval_low(120)
        self.version_selector.update_switch_interval_high(300)
        self.version_selector.timer_spinbox1.setValue(120)
        self.version_selector.timer_spinbox2.setValue(300)

    def set_museum_preset(self):
        """Apply museum environment preset settings."""
        self.version_selector.update_switch_interval_low(1)
        self.version_selector.update_switch_interval_high(5)
        self.version_selector.timer_spinbox1.setValue(1)
        self.version_selector.timer_spinbox2.setValue(5)

    def set_fair_preset(self):
        """Apply fair environment preset settings."""
        self.version_selector.update_switch_interval_low(0.5)
        self.version_selector.update_switch_interval_high(1)
        self.version_selector.timer_spinbox1.setValue(0.5)
        self.version_selector.timer_spinbox2.setValue(1)

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