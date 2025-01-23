"""
Settings control panel for configuring display parameters, timings, 
and debug options.
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from display_control_panel import DisplayControlPanelWidget

class SettingsControlPanel(QWidget):
    def __init__(self, display, main_display, version_selector, parent=None):
        """
        Initialize settings control panel.
        
        Args:
            display: Display manager reference  
            main_display: Main display window reference
            version_selector: Version selector instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.display = display
        self.main_display = main_display
        self.version_selector = version_selector
        
        # Create panel without version selection
        self.panel = DisplayControlPanelWidget(display, main_display, version_selector)
        
        # Remove version selection elements
        layout = self.panel.layout()
        while layout.itemAt(0) and layout.itemAt(0).widget():
            layout.itemAt(0).widget().setParent(None)
            
        self.setLayout(layout)
        self.setWindowTitle("Settings")

    def closeEvent(self, event):
        """Handle panel close."""
        self.main_display.settings_panel = None
        self.main_display.setCursor(Qt.BlankCursor)
        self.main_display.activateWindow()
        event.accept()