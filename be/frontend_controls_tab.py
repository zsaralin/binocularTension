"""
Frontend controls tab with settings management and initialization from config.
Provides a scrollable interface for numerous control settings.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QLineEdit, QSpacerItem, QSizePolicy,
    QPushButton, QMessageBox, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer
import socket
import json
import os

from slider_group import SliderGroup

class FrontendSliderGroup(SliderGroup):
    """
    Frontend slider with reliable value broadcasting.
    Extends base SliderGroup to add network broadcasting capability.
    """
    
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
    Provides a scrollable interface for numerous slider controls.
    
    Attributes:
        sliders (dict): Collection of slider widgets indexed by variable name
    """
    
    def __init__(self, preset_listener=None, parent=None):
        super().__init__(parent)
        self.sliders = {}

        self.preset_listener = preset_listener

        if preset_listener:
            preset_listener.frontend_value_received.connect(self.update_slider)

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the UI components with scrolling support."""
        # Main layout for the tab
        main_layout = QVBoxLayout(self)

        # Create scroll area and its widget
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create content widget to hold all controls
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        
        # Add all the slider groups
        self.add_blink_section()
        self.add_jitter_section()
        self.add_sleep_section()
        self.add_display_section()
        self.add_y_movement_section()

        # Add save button with feedback
        save_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Frontend Config")
        self.save_button.clicked.connect(self.save_frontend_config)
        self.restore_button = QPushButton("Restore to Defaults")
        self.restore_button.clicked.connect(self.restore_default_settings)
        self.save_status = QLabel("")
        save_layout.addWidget(self.save_button)
        save_layout.addWidget(self.restore_button)
        save_layout.addWidget(self.save_status)
        self.layout.addLayout(save_layout)

        # Add spacing at the bottom
        self.layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # Set the scroll area's widget and add to main layout
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def add_section_header(self, text):
        """Add a section header with consistent styling."""
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(label)

    def add_blink_section(self):
        """Add blink settings section."""
        self.add_section_header("Blink Settings")
        
        self.add_slider_group(
            "min_blink_interval", "Min Blink Interval (s)", 3.0,
            1.0, 20.0, 0.1
        )
        self.add_slider_group(
            "max_blink_interval", "Max Blink Interval (s)", 8.0,
            1.0, 20.0, 0.1
        )
        self.add_slider_group(
            "forced_blink_x_thres", "Forced Blink X Thres", 10.0,
            1.0, 35.0, 1
        )
        self.add_slider_group(
            "blink_speed", "Blink Speed", 5.0,
            1.0, 10.0, 1.0
        )

    def add_jitter_section(self):
        """Add jitter settings section."""
        self.add_section_header("Jitter Settings")
        self.add_slider_group(
            "nervousness", "Nervousness", 0.8, 0.0, 1.0, 0.1
        )
        # Basic jitter controls
        self.add_slider_group(
            "jitter_start_delay", "Initial Delay (s)", 0.5,
            0.1, 5.0, 0.1
        )
        self.add_slider_group(
            "large_jitter_start_delay", "Large Pattern Delay (s)", 60.0,
            1.0, 300.0, 1.0
        )
        self.add_slider_group(
            "min_jitter_interval", "Min Interval (s)", 3.0,
            0.1, 10.0, 0.1
        )
        self.add_slider_group(
            "max_jitter_interval", "Max Interval (s)", 6.0,
            0.1, 20.0, 0.1
        )
        self.add_slider_group(
            "min_jitter_speed", "Min Speed (ms)", 500,
            100, 1000, 10
        )
        self.add_slider_group(
            "max_jitter_speed", "Max Speed (ms)", 800,
            100, 2000, 10
        )

    def add_sleep_section(self):
        """Add sleep settings section."""
        self.add_section_header("Sleep Settings")
        
        self.add_slider_group(
            "min_sleep_timeout", "Min Sleep Timeout (s)", 10.0,
            1.0, 300.0, 1.0
        )
        self.add_slider_group(
            "max_sleep_timeout", "Max Sleep Timeout (s)", 12.0,
            1.0, 300.0, 1.0
        )
        self.add_slider_group(
            "min_random_wakeup", "Min Wakeup Interval (s)", 35.0,
            1.0, 300.0, 1.0
        )
        self.add_slider_group(
            "max_random_wakeup", "Max Wakeup Interval (s)", 65.0,
            1.0, 300.0, 1.0
        )
        self.add_slider_group(
            "display_off_timeout", "Display Off Timeout (h)", 2.0,
            0.1, 24.0, 0.1
        )

    def add_display_section(self):
        """Add display settings section."""
        self.add_section_header("Display Settings")
        
        self.add_slider_group(
            "stretch_x", "Horizontal Stretch", 1.0,
            1.0, 1.5, 0.01
        )
        self.add_slider_group(
            "stretch_y", "Vertical Stretch", 1.0,
            1.0, 1.5, 0.01
        )
        self.add_slider_group(
            "rotate", "Rotation (degrees)", 0.0,
            -5.0, 5.0, 0.1
        )

    def add_y_movement_section(self):
        """Add display settings section."""
        self.add_section_header("Y Movement Settings")
        self.add_slider_group(
            "smooth_y", "Y-Movement Smoothing", 10.0,
            0.0, 100.0, 1.0
        )
        self.add_slider_group(
            "left_cutoff_x", "Left Cutoff X", 5.0,
            0.0, 39.0, 1
        )
        self.add_slider_group(
            "right_cutoff_x", "Right Cutoff X", 34.0,
            0.0, 39.0, 1
        )



    def add_slider_group(self, variable_name, label_text,
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
        self.layout.addWidget(group)
        self.sliders[variable_name] = group


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


    def restore_default_settings(self):
        """
        Load and apply settings from default_display_config.json.
        Updates UI sliders and broadcasts new values to frontend.
        """
        try:
            # Load default settings
            with open('../fe/default_display_config.json', 'r') as f:
                defaults = json.load(f)
                
            # Update each slider with default value and broadcast
            for var_name, slider in self.sliders.items():
                if var_name in defaults:
                    # Update slider UI
                    slider.set_value(defaults[var_name])
                    # Ensure value is broadcast
                    slider.broadcast_value(defaults[var_name])
                    
            # Show success message
            self.save_status.setText("Defaults Restored!")
            self.save_status.setStyleSheet("color: green")
            QTimer.singleShot(3000, lambda: self.save_status.setText(""))
            
            # Trigger save to persist changes
            self.save_frontend_config()
            
        except FileNotFoundError:
            print("Default config file not found")
            self.save_status.setText("Default Config Not Found!")
            self.save_status.setStyleSheet("color: red")
            QTimer.singleShot(3000, lambda: self.save_status.setText(""))
        except json.JSONDecodeError as e:
            print(f"Error parsing default config: {e}")
            self.save_status.setText("Invalid Default Config!")
            self.save_status.setStyleSheet("color: red")
            QTimer.singleShot(3000, lambda: self.save_status.setText(""))
        except Exception as e:
            print(f"Unexpected error restoring defaults: {e}")
            self.save_status.setText("Restore Failed!")
            self.save_status.setStyleSheet("color: red")
            QTimer.singleShot(3000, lambda: self.save_status.setText(""))


    def update_slider(self, variable_name: str, value: float):
        """
        Update a slider's value when a preset value is received.
        
        Args:
            variable_name (str): Name of the slider to update
            value (float): New value to set
        """
        if variable_name in self.sliders:
            slider_group = self.sliders[variable_name]
            slider_group.set_value(value)
            print(f"Updated slider {variable_name} to {value}")
        else:
            print(f"No slider found for {variable_name}")