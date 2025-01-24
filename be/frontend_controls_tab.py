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
import socket
import json

from slider_group import SliderGroup


class FrontendSliderGroup(SliderGroup):
    """Frontend slider with reliable value broadcasting."""
    
    def __init__(self, variable_name: str, label_text: str, initial_value: float,
                 min_val: float, max_val: float, step: float, 
                 broadcast_socket=None, parent=None):
        """
        Initialize frontend slider.
        
        Args:
            variable_name: Name of controlled variable
            broadcast_socket: UDP socket for sending updates
            Other args: Same as SliderGroup
        """
        super().__init__(label_text, initial_value, min_val, max_val, step, parent)
        self.variable_name = variable_name
        self.broadcast_socket = broadcast_socket or self._create_broadcast_socket()
        
        # Override slider signal to include broadcast
        self.slider.valueChanged.disconnect()
        self.slider.valueChanged.connect(self.on_slider_changed_with_broadcast)

    def _create_broadcast_socket(self):
        """Create UDP broadcast socket."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return sock

    def broadcast_value(self, value: float):
        """Broadcast value update via UDP."""
        message = {
            "variable": self.variable_name,
            "value": value
        }
        try:
            self.broadcast_socket.sendto(
                json.dumps(message).encode(),
                ('localhost', 12345)
            )
        except Exception as e:
            print(f"Broadcast error for {self.variable_name}: {e}")

    def on_slider_changed_with_broadcast(self, slider_pos: float):
        """Handle slider change and broadcast update."""
        new_val = slider_pos * self.step
        self.value_label.setText(f"{new_val:.1f}")
        self.line_edit.setText(f"{new_val:.1f}")
        self.broadcast_value(new_val)
        
    



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
            layout, "nervousness",
            "Nervousness", 5.0, 0.0, 10.0, 0.1
        )

        self.add_save_button(layout)

        # Add vertical spacer
        layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        self.setLayout(layout)

    def add_slider_group(self, layout, variable_name, label_text,
                        initial_value, min_val, max_val, step):
        """Add a frontend slider group."""
        group = FrontendSliderGroup(
            variable_name=variable_name,
            label_text=label_text,
            initial_value=initial_value,
            min_val=min_val,
            max_val=max_val,
            step=step,
            parent=self
        )
        layout.addWidget(group)
        self.sliders[variable_name] = group

    def add_save_button(self, layout):
        """Add a save button to the layout."""
        save_button = QPushButton("Save Frontend Config")
        save_button.clicked.connect(self.save_frontend_config)
        layout.addWidget(save_button)

    def save_frontend_config(self):
        """Handle frontend config saving."""
        print("frontend saving")