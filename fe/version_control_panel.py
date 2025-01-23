from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

class VersionControlPanel(QWidget):
    def __init__(self, main_display, version_selector, parent=None):
        super().__init__(parent)
        self.main_display = main_display
        self.version_selector = version_selector
        
        self.setWindowTitle("Version Selection")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Version selector controls
        self.version_selector.setup_ui(layout)
        
        # Preset controls
        preset_label = QLabel("Pre Selected Settings")
        preset_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preset_label)
        
        preset_layout = QHBoxLayout()
        
        home_button = QPushButton("Home")
        home_button.clicked.connect(self.set_home_preset)
        
        fair_button = QPushButton("Fair")
        fair_button.clicked.connect(self.set_fair_preset)
        
        preset_layout.addWidget(home_button)
        preset_layout.addWidget(fair_button)
        
        layout.addLayout(preset_layout)
        self.setLayout(layout)

    def set_home_preset(self):
        self.version_selector.update_switch_interval_low(10)
        self.version_selector.update_switch_interval_high(30)
        self.version_selector.timer_spinbox1.setValue(10)
        self.version_selector.timer_spinbox2.setValue(30)

    def set_fair_preset(self):
        self.version_selector.update_switch_interval_low(1)
        self.version_selector.update_switch_interval_high(3)
        self.version_selector.timer_spinbox1.setValue(1)
        self.version_selector.timer_spinbox2.setValue(3)

    def closeEvent(self, event):
        self.version_selector.save_config()
        self.main_display.version_panel = None
        self.main_display.setCursor(Qt.BlankCursor)
        self.main_display.activateWindow()
        event.accept()