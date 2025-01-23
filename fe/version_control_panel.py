"""
Version selection control panel that allows switching between male/female versions
and configuring auto-switch timing.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

class VersionControlPanel(QWidget):
    def __init__(self, main_display, version_selector, parent=None):
        """
        Initialize version control panel.
        
        Args:
            main_display: Main display window reference
            version_selector: Version selector instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.main_display = main_display
        self.version_selector = version_selector
        
        self.setWindowTitle("Version Selection")
        self.init_ui()

    def init_ui(self):
        """Set up the version control panel UI."""
        layout = QVBoxLayout()
        self.version_selector.setup_ui(layout)
        self.setLayout(layout)
        
    def closeEvent(self, event):
        """Handle panel close event."""
        self.main_display.version_panel = None
        self.main_display.setCursor(Qt.BlankCursor)
        self.main_display.activateWindow()
        event.accept()