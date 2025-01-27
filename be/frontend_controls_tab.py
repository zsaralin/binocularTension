"""
Frontend controls tab with settings management and initialization from config.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QLineEdit, QSpacerItem, QSizePolicy,
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
import socket
import json
import os

from slider_group import SliderGroup

class FrontendSliderGroup(SliderGroup):
    """Frontend slider with reliable value broadcasting."""
    
    def __init__(self, variable_name: str, label_text: str, initial_value: float,
                 min_val: float, max_val: float, step: float, 
                 broadcast_socket=None, parent=None):
        """
        Initialize frontend slider with network broadcasting capability.
        
        Args:
            variable_name (str): Name of the variable this slider controls
            label_text (str): Display label for the slider
            initial_value (float): Starting value
            min_val (float): Minimum allowed value
            max_val (float): Maximum allowed value
            step (float): Step size for slider movement
            broadcast_socket (socket, optional): UDP socket for broadcasting updates
            parent (QWidget, optional): Parent widget
        """
        super().__init__(label_text, initial_value, min_val, max_val, step, parent)
        self.variable_name = variable_name
        self.broadcast_socket = broadcast_socket or self._create_broadcast_socket()
        
        # Override slider signal to include broadcast
        self.slider.valueChanged.disconnect()
        self.slider.valueChanged.connect(self.on_slider_changed_with_broadcast)

    def _create_broadcast_socket(self):
        """Create UDP socket for broadcasting updates."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return sock

    def broadcast_value(self, value: float):
        """Broadcast a value update over UDP."""
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
        """Handle slider changes and broadcast updates."""
        new_val = slider_pos * self.step
        self.value_label.setText(f"{new_val:.1f}")
        self.line_edit.setText(f"{new_val:.1f}")
        self.broadcast_value(new_val)

    def set_value_without_broadcast(self, value: float):
        """
        Set the slider value without triggering a broadcast.
        Used for initialization from config.
        
        Args:
            value (float): New value to set
        """
        # Temporarily disconnect the broadcast
        self.slider.valueChanged.disconnect()
        
        # Update both slider and text box
        self.set_value(value)
        self.value_label.setText(f"{value:.1f}")
        self.line_edit.setText(f"{value:.1f}")
        
        # Reconnect the broadcast
        self.slider.valueChanged.connect(self.on_slider_changed_with_broadcast)

class FrontendControlsTab(QWidget):
    """
    Frontend controls tab with configuration management.
    
    Attributes:
        sliders (dict): Collection of slider widgets indexed by variable name
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sliders = {}
        self.init_ui()
        self.load_settings()  # Load settings after UI is initialized

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()

        # Add slider groups with default values
        # These will be updated from config after creation
        self.add_slider_group(
            layout, "nervousness",
            "Nervousness", 0.8,  # Default value
            0.0, 1.0, 0.1
        )
        

        label = QLabel("Blink Settings")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        # Min blink interval
        self.add_slider_group(
            layout, "min_blink_interval",
            "Min Blink Interval (s)", 3.0,
            1.0, 20.0, 0.1
        )

        # Max blink interval
        self.add_slider_group(
            layout, "max_blink_interval",
            "Max Blink Interval (s)", 8.0,
            1.0, 20.0, 0.1
        )

        # Blink speed
        self.add_slider_group(
            layout, "blink_speed",
            "Blink Speed", 5.0,
            1.0, 10.0, 1.0
        )


        label = QLabel("Jitter Settings") 
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        # Basic jitter controls
        self.add_slider_group(
            layout, "jitter_start_delay",
            "Initial Delay (s)", 0.5,
            0.1, 5.0, 0.1
        )

        self.add_slider_group(
            layout, "large_jitter_start_delay",
            "Large Pattern Delay (s)", 60.0,
            1.0, 300.0, 1.0
        )

        # Jitter timing
        self.add_slider_group(
            layout, "min_jitter_interval",
            "Min Interval (s)", 3.0,
            0.1, 10.0, 0.1
        )

        self.add_slider_group(
            layout, "max_jitter_interval",
            "Max Interval (s)", 6.0,
            0.1, 20.0, 0.1
        )

        # Jitter speed
        self.add_slider_group(
            layout, "min_jitter_speed",
            "Min Speed (ms)", 500,
            100, 1000, 10
        )

        self.add_slider_group(
            layout, "max_jitter_speed",
            "Max Speed (ms)", 800,
            100, 2000, 10
        )

        label = QLabel("Sleep Settings")
        label.setStyleSheet("font-weight: bold;") 
        layout.addWidget(label)

        # Basic sleep timeouts
        self.add_slider_group(
            layout, "min_sleep_timeout",
            "Min Sleep Timeout (s)", 10.0,
            1.0, 300.0, 1.0
        )

        self.add_slider_group(
            layout, "max_sleep_timeout",
            "Max Sleep Timeout (s)", 12.0,
            1.0, 300.0, 1.0
        )

        # Random wakeup settings
        self.add_slider_group(
            layout, "min_random_wakeup",
            "Min Wakeup Interval (s)", 35.0,
            1.0, 300.0, 1.0
        )

        self.add_slider_group(
            layout, "max_random_wakeup", 
            "Max Wakeup Interval (s)", 65.0,
            1.0, 300.0, 1.0
        )

        # Display timeout
        self.add_slider_group(
            layout, "display_off_timeout",
            "Display Off Timeout (h)", 2.0,
            0.1, 24.0, 0.1
        )


        label = QLabel("Display Settings")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        self.add_slider_group(
            layout, "stretch_x",
            "Horizontal Stretch", 1.0,
            1.0, 1.5, 0.01
        )

        self.add_slider_group(
            layout, "stretch_y",
            "Vertical Stretch", 1.0,
            1.0, 1.5, 0.01
        )

        # Image smoothing and rotation
        self.add_slider_group(
            layout, "smooth_y",
            "Y-Movement Smoothing", 10.0,
            0.0, 100.0, 1.0
        )

        self.add_slider_group(
            layout, "rotate",
            "Rotation (degrees)", 0.0,
            -5.0, 5.0, 0.1
        )

        # Add save button with feedback
        save_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Frontend Config")
        self.save_button.clicked.connect(self.save_frontend_config)
        self.save_status = QLabel("")
        save_layout.addWidget(self.save_button)
        save_layout.addWidget(self.save_status)
        layout.addLayout(save_layout)

        # Add vertical spacer
        layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        self.setLayout(layout)

    def load_settings(self):
        """Load settings from config file and update sliders."""
        try:
            if os.path.exists('../fe/display_config.json'):
                with open('../fe/display_config.json', 'r') as f:
                    config = json.load(f)
                    
                # Update each slider with its saved value
                for var_name, slider in self.sliders.items():
                    if var_name in config:
                        slider.set_value_without_broadcast(config[var_name])
                print("Settings loaded from config")
            else:
                print("No config file found, using defaults")
        except Exception as e:
            print(f"Error loading settings: {e}")

    def add_slider_group(self, layout, variable_name, label_text,
                        initial_value, min_val, max_val, step):
        """
        Add a new slider group to the layout.
        
        Args:
            layout (QLayout): Layout to add the slider to
            variable_name (str): Name of the variable this slider controls
            label_text (str): Display label for the slider
            initial_value (float): Starting value
            min_val (float): Minimum allowed value
            max_val (float): Maximum allowed value
            step (float): Step size for slider movement
        """
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

    def save_frontend_config(self):
        """Send save command to socket listener."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            message = {"command": "save"}
            sock.sendto(json.dumps(message).encode(), ('localhost', 12345))
            
            print("Save command sent successfully")
            sock.close()
            
            # Update save status
            self.save_status.setText("Saved!")
            self.save_status.setStyleSheet("color: green")
            QTimer.singleShot(3000, lambda: self.save_status.setText(""))
        except Exception as e:
            print(f"Error sending save command: {e}")
            self.save_status.setText("Save Failed!")
            self.save_status.setStyleSheet("color: red")
            QTimer.singleShot(3000, lambda: self.save_status.setText(""))