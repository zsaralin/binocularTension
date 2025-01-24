"""
Provides an additional tab for the control panel with supplementary settings.
This tab can be extended with more functionality as needed.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QLineEdit, QSpacerItem, QSizePolicy,
    QPushButton
)
from PyQt5.QtCore import Qt

from slider_group import SliderGroup

class FrontendSliderGroup(SliderGroup):
    """
    Frontend-specific slider group extending base SliderGroup.
    Can be customized with frontend-specific functionality.
    
    Inherits all attributes and methods from SliderGroup.
    """
    
    def __init__(self, label_text: str, initial_value: float,
                 min_val: float, max_val: float, step: float, parent=None):
        super().__init__(label_text, initial_value, min_val, max_val, step, parent)
        
    


class FrontendControlsTab(QWidget):
    """
    Additional controls tab with sample SliderGroup implementation.
    
    Attributes:
        sliders (dict): Collection of SliderGroup widgets
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sliders = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()

        # Add example slider groups
        self.add_slider_group(
            layout, "sample_setting",
            "Sample Setting", 5.0, 0.0, 10.0, 0.1
        )

        self.add_save_button(layout)

        # Add vertical spacer
        layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        self.setLayout(layout)

    def add_slider_group(self, layout, setting_name, label_text,
                        initial_value, min_val, max_val, step):
        """
        Add a new slider group to the layout.
        
        Args:
            layout: Layout to add slider to
            setting_name: Identifier for the slider
            label_text: Display label
            initial_value: Starting value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            step: Increment size
        """
        group = FrontendSliderGroup(
            label_text, initial_value, min_val, max_val, step, parent=self
        )
        layout.addWidget(group)
        self.sliders[setting_name] = group

    def add_save_button(self, layout):
        """Add a save button to the layout."""
        save_button = QPushButton("Save Frontend Config")
        save_button.clicked.connect(self.save_frontend_config)
        layout.addWidget(save_button)

    def save_frontend_config(self):
        """Handle frontend config saving."""
        print("frontend saving")