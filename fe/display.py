import sys
import os
import socket
import threading
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

from display_control_panel import DisplayControlPanelWidget
from display_live_config import DisplayLiveConfig
from debug_mode import DebugModeManager
from blink_sleep_manager import BlinkSleepManager

import time
import random
import subprocess
import re  # Import re module for regular expressions

from version_control_panel import VersionControlPanel 
from settings_control_panel import SettingsControlPanel

from version_selector import VersionSelector

from socket_listener_service import SocketListenerService

def get_largest_display():
    app = QApplication.instance() or QApplication(sys.argv)
    screens = app.screens()
    largest_screen = max(screens, key=lambda screen: screen.size().width() * screen.size().height()) # should be max
    return largest_screen

class FullScreenBlinkApp(QWidget):
    update_image_signal = pyqtSignal(str)

    def __init__(self, image_folders):
        super().__init__()

        self.current_folder = "brown"  # Start with "brown" folder
        self.current_filename = "bt_20_cso.jpg"
        self.update_in_progress = False  # Flag to prevent updates during transitions
        self.live_config = DisplayLiveConfig.get_instance() # Load live config values

        
        self.label = QLabel(self)
        self.filename_label = QLabel(self)
        self.filename_label.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        self.filename_label.setStyleSheet("font-size: 1gpx; color:  rgba(0, 0, 0, 0); background-color: rgba(0, 0, 0, 0); padding: 5px;")
        self.filename_label.setWordWrap(True)
        self.debug_mode_manager = DebugModeManager(self)
        self.setCursor(Qt.BlankCursor)

        
        self.image_folders = {  # Store folders with labels
            "brown": image_folders[0],
            "blue": image_folders[1],
        }
        # Load images
        self.image_filenames = {"brown": [], "blue": []}
        self.images = {"brown": {}, "blue": {}}
        self.load_images()

        
        
        self.blink_sleep_manager = BlinkSleepManager(self)
        self.blink_sleep_manager.sleep_manager.turn_on_display_()

        self.version_selector = VersionSelector(self)  
        
        self.stabilized_y = None  # Stores stabilized y value

        self.y_history = []  # Stores last 5 y values
    
        # Set up window
        largest_screen = get_largest_display()
        self.move(largest_screen.geometry().x(), largest_screen.geometry().y())
        self.setWindowFlags(Qt.FramelessWindowHint)



        # Display initial image and set up signal for server updates
        self.display_image(self.current_filename)
        self.update_image_signal.connect(self.update_display_image)

        # Initialize control panel
        self.control_panel = None

        self.update_skip_count = 0 

        # self.showFullScreen()
        # self.activateWindow()  # Make this window the active window
        # self.setFocus(Qt.OtherFocusReason)  # Give this window keyboard focus
        # self.setWindowState(self.windowState() | ~Qt.WindowMinimized | Qt.WindowActive)  # Bring window to front
        # self.raise_()
        

        # Cheating way of activating all of the config settings which currently only activate at 
        self.toggle_control_panel()
        self.toggle_control_panel()

        self.selector = VersionSelector(self)

        self.socket_service = SocketListenerService()
        self.socket_service.value_received.connect(self.handle_frontend_update)
        self.socket_service.start()

        self._bring_to_front()
        
    def load_images(self):
        for folder_key, folder_path in self.image_folders.items():
            if os.path.exists(folder_path):
                for filename in os.listdir(folder_path):
                    if filename.endswith(".jpg"):
                        image_path = os.path.join(folder_path, filename)
                        print(image_path)
                        pixmap = QPixmap(image_path)
                        self.image_filenames[folder_key].append(filename)
                        self.images[folder_key][filename] = pixmap
        if self.image_filenames["brown"]:  # Start with the first image in "brown"
            self.display_image(self.current_filename)

    def extract_x_from_filename(self, filename):
        """Extract the x value from the filename."""
        match = re.match(r"bt_(\d+)_.*\.jpg", filename)
        if match:
            x_value = int(match.group(1))
            return x_value
        else:
            return None
        
    def extract_y_from_filename(self, filename):
        """Extract the y value from the filename."""
        match = re.match(r"bt_\d+_.(\w)\w*\.jpg", filename)  # The `.` before `(\w)` ensures we get the second character
        if match:
            return match.group(1)  # Extracts the second letter after the number
        else:
            return None
 
    def display_image(self, filename):
        image_path = os.path.join(self.image_folders[self.current_folder], filename)
        if os.path.exists(image_path):
            pixmap = self.images[self.current_folder].get(filename)
            if not pixmap:
                pixmap = QPixmap(image_path)
                self.images[self.current_folder][filename] = pixmap

            # Retrieve stretch factors from LiveConfig
            stretch_x = self.live_config.stretch_x  # Horizontal stretch factor
            stretch_y = self.live_config.stretch_y # Vertical stretch factor

            # Calculate the new size based on stretch factors
            original_size = pixmap.size()
            new_width = int(original_size.width() * stretch_x)
            new_height = int(original_size.height() * stretch_y)

            # Resize the pixmap with the new dimensions
            stretched_pixmap = pixmap.scaled(new_width, new_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

            # Get the size of the current widget (self)
            widget_width = self.width()
            widget_height = self.height()

            # Calculate the top-left position for the image to be centered
            center_x = (widget_width - new_width) // 2
            center_y = (widget_height - new_height) // 2

            # Update the label geometry and display the stretched image
            self.label.setGeometry(center_x, center_y, new_width, new_height)
            self.label.setPixmap(stretched_pixmap)
            self.filename_label.setText(filename)
            self.filename_label.adjustSize()
            if not filename[-5].lower() == "h":  # Check if the character before ".jpg" is NOT 'h'
                self.current_filename = filename
        else:
            print(f"Image not found: {image_path}")

    def update_display_image(self, data):
        parts = data.split("|")
        if len(parts) != 2:
            print(f"Invalid data format received: {data}")
            return

        filename, is_new_movement = parts
        is_new_movement = is_new_movement == "True"

        if self.blink_sleep_manager.sleep_manager.display_off:
            self.blink_sleep_manager.sleep_manager.turn_on_display_()
        if self.blink_sleep_manager.sleep_manager.in_sleep_mode:
            print("Exiting sleep mode.")
            self.blink_sleep_manager.sleep_manager.exit_sleep_mode()
        if self.update_in_progress:
            print("Update in progress, ignoring new update.")
            # self.update_skip_count += 1
            if self.update_skip_count == 3:
                self.update_skip_count = 0
                self.update_in_progress = False
            return

        current_x = self.extract_x_from_filename(self.current_filename)
        new_x = self.extract_x_from_filename(filename)

        current_y = self.stabilized_y if self.stabilized_y else self.extract_y_from_filename(self.current_filename)
        new_y = self.extract_y_from_filename(filename)

        # print('new:', filename, 'old:', self.current_filename, 'is_new_movement:', is_new_movement)
        if is_new_movement:
            print("🔹 New movement detected! Immediately updating.")
            self.stabilized_y = new_y  # Bypass stabilization for new movements
        else:
            # Track last `consistent_y_threshold` y-values
            self.y_history.append(new_y)
            if len(self.y_history) > self.live_config.smooth_y:
                self.y_history.pop(0)

            # **Only update stabilized_y if all recent y-values match**
            if len(set(self.y_history)) == 1:
                self.stabilized_y = new_y  # Update to new y once stable
            # else:
                # print(f"Y is not stable yet (current: {self.stabilized_y}, new: {new_y})")
                # new_y = self.stabilized_y  # Use the last stable y instead

        # **Fix: Ensure filename includes the stabilized y-value**
        filename = re.sub(r'bt_(\d+)_c([usd])(\w).jpg', f'bt_{new_x}_c{self.stabilized_y}\\3.jpg', filename)
        if filename == self.current_filename:
            return
        if current_x is not None and new_x is not None and not self.update_in_progress:
            delta = abs(new_x - current_x)
            if delta > 10:
                self.update_in_progress = True

                print("🔹 Large movement detected! Using new Y without stabilization.")
                self.stabilized_y = new_y  # Force using new Y if movement is large

            # **Fix: Ensure filename includes the correct Y value**
            filename = re.sub(r'bt_(\d+)_c([usd])(\w).jpg', f'bt_{new_x}_c{self.stabilized_y}\\3.jpg', filename)
            if filename == self.current_filename:
                return

            if delta > 10 or (current_y in ['u', 's'] and self.stabilized_y == 'd') or (current_y == 'd' and self.stabilized_y in ['u', 's']):
                self.blink_sleep_manager.jitter_manager.stop_all_jitter()
                self.update_in_progress = True

                if random.random() < 1:
                    print("Simulating blink with position change." , filename)
                    try:
                        self.current_filename = filename  # Ensure it's updated before blinking
                        self.blink_sleep_manager.jitter_manager.stop_all_jitter()

                        self.blink_sleep_manager.blink_manager.simulate_blink(new_filename=filename)
                        blink_speed = self.live_config.blink_speed  # Higher is faster
                        base_delay = 800  # Base delay in ms for the slowest speed
                        total_blink_duration = int((base_delay / blink_speed) * 5)  # 5 steps in simulate_blink
                        QTimer.singleShot(total_blink_duration, lambda: self.finish_update(filename))
                        self.blink_sleep_manager.jitter_manager.stop_all_jitter()

                    except Exception as e:
                        print(f"Error during update: {e}")
            else:

                if self.blink_sleep_manager.sleep_manager.in_sleep_mode:
                    print("Exiting sleep mode.")
                    self.blink_sleep_manager.sleep_manager.exit_sleep_mode()
                if not self.blink_sleep_manager.blink_manager.is_blinking and not self.update_in_progress:
                    print(filename)
                    self.display_image(filename)
                    self.current_filename = filename
                    self.blink_sleep_manager.update_last_image_time()

    def finish_update(self, filename):
        """Reset the update_in_progress flag after transition."""
        self.update_in_progress = False
        self.current_filename = filename
        self.blink_sleep_manager.jitter_manager.stop_all_jitter()

        print("Finished large jump transition.")
        

    def switch_image_folder(self, folder_name):
        if folder_name not in self.image_folders:
            print(f"Invalid folder name: {folder_name}. Must be 'brown' or 'blue'.")
            return
        self.current_folder = folder_name
        print(f"Switched to folder: {folder_name}")
        if self.image_filenames[folder_name]:
            self.display_image(self.current_filename)

    def start_server_thread(self, host, port):
        def listen_for_commands():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.bind((host, port))
                server_socket.listen()
                print(f"Server listening on {host}:{port}")
                while True:
                    conn, addr = server_socket.accept()
                    with conn:
                        data = conn.recv(1024).decode().strip()
                        if data:
                            if data.startswith("switch:"):  # Check for folder switch command
                                folder_name = data.split(":")[1].strip()
                                if folder_name in self.image_folders:
                                    self.switch_image_folder(folder_name)
                                    print(f"Switched to folder: {folder_name}")
                                else:
                                    print(f"Invalid folder name received: {folder_name}")
                            elif not self.debug_mode_manager.debug_mode:
                                # Regular image update command
                                self.update_image_signal.emit(data)
                            else:
                                # Expecting "filename|new" or "filename|old"
                                parts = data.split("|")
                                if len(parts) == 2:
                                    filename, movement_status = parts
                                    is_new_movement = movement_status == "new"
                                    self.update_image_signal.emit(f"{filename}|{is_new_movement}")
                                else:
                                    print(f"Invalid data format received: {data}")
        thread = threading.Thread(target=listen_for_commands, daemon=True)
        thread.start()

    def toggle_control_panel(self):
        """
        Show/hide the control panel. 
        IMPORTANT: Pass 'self.version_selector' so the control panel uses the same instance.
        """
        if self.control_panel is None:
            self.control_panel = DisplayControlPanelWidget(
                display=self.debug_mode_manager, 
                main_display=self,               # so it can call self.switch_image_folder
                version_selector=self.version_selector
            )
            self.control_panel.show()
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.BlankCursor)
            self.control_panel.close()
            self.control_panel = None
            

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_U:
            self.toggle_version_panel()
        elif key == Qt.Key_Escape:
            sys.exit()
            # self.close()
        elif key == Qt.Key_Left:
            self.switch_image_folder("blue")
            if self.version_selector:
                self.version_selector.switch_folder("blue")
                self.version_selector.stop_auto_switch()
        elif key == Qt.Key_Right:
            self.switch_image_folder("brown")
            if self.version_selector:
                self.version_selector.switch_folder("brown")
                self.version_selector.stop_auto_switch()
        elif key == Qt.Key_Down or key == Qt.Key_Up:
            self.version_selector.handle_auto_switch(True)
        else:
            super().keyPressEvent(event)

    def toggle_version_panel(self):
        """
        Toggle version selection panel visibility.
        
        This method handles both opening and closing the version control panel:
        - If the panel doesn't exist or is closed, it creates and shows a new one
        - If the panel exists and is visible, it closes and destroys it
        - Updates cursor visibility based on panel state
        - Properly maintains panel reference to prevent memory leaks
        """
        print("Toggling version panel.")
        if not hasattr(self, 'version_panel') or self.version_panel is None:
            # Create and show new panel
            self.version_panel = VersionControlPanel(self, self.version_selector)
            self.version_panel.show()
            self.setCursor(Qt.ArrowCursor)
        else:
            # Close existing panel
            if self.version_panel.isVisible():
                self.version_panel.close()
                self.version_panel = None
                self.setCursor(Qt.BlankCursor)

    def toggle_settings_panel(self):
        """Toggle settings panel triggered by 'g' key."""
        if not hasattr(self, 'settings_panel') or self.settings_panel is None:
            self.settings_panel = SettingsControlPanel(
                display=self.debug_mode_manager,
                main_display=self,
                version_selector=self.version_selector
            )
            self.settings_panel.show()
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.BlankCursor) 
            self.settings_panel.close()
            self.settings_panel = None

    def _bring_to_front(self):
        """Bring window to foreground."""
        print("Bringing window to front.")
        """
        Bring window to foreground and ensure it's above taskbar.
        Uses multiple techniques to guarantee window activation and proper z-order.
        """
        self.showFullScreen()  # Show full screen
        
        # Set window flags to stay on top temporarily
        # self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setFocusPolicy(Qt.StrongFocus)
        self.show()
        
        self.activateWindow()
        self.raise_()
        self.showFullScreen()
        # Clear the stay on top flag after a brief delay
        QTimer.singleShot(100, lambda: self._clear_top_flag())
        
        # Additional focus request
        QTimer.singleShot(200, self.activateWindow)


    def _clear_top_flag(self):
        """Clear the stay on top flag."""
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def handle_frontend_update(self, variable_name: str, value: float):
        """
        Handle frontend settings updates from socket listener.
        Updates both the live config and relevant managers.
        
        Args:
            variable_name (str): Name of the setting being updated
            value (float): New value for the setting
        """
        print(f"Frontend update received: {variable_name} = {value}")

        if variable_name == "focus_command":
            # self.activateWindow()
            # self.raise_()
            # self.showFullScreen()
            self._bring_to_front()
            return
        
        # Update live config
        if hasattr(self.live_config, variable_name):
            setattr(self.live_config, variable_name, value)
            
            # Handle special cases that need manager updates
            if variable_name == "nervousness":
                # Update jitter manager's nervousness factor
                if hasattr(self.blink_sleep_manager, 'jitter_manager'):
                    print(f"Updating jitter manager nervousness to {value}")
                    self.blink_sleep_manager.jitter_manager.nervousness = value
                    
                # Since nervousness affects jitter timing, restart the jitter process
                self.blink_sleep_manager.jitter_manager.stop_all_jitter()
                self.blink_sleep_manager.jitter_manager.start_jitter_process()

            elif variable_name in ["min_blink_interval", "max_blink_interval"]:
                if hasattr(self.blink_sleep_manager, 'blink_manager'):
                    print(f"Updating blink intervals")
                    self.blink_sleep_manager.blink_manager.on_blink_interval_changed()

            elif variable_name == "blink_speed":
                if hasattr(self.blink_sleep_manager, 'blink_manager'):
                    print(f"Updating blink speed to {value}")

            elif variable_name in [
                "jitter_start_delay",
                "large_jitter_start_delay",
                "min_jitter_interval", 
                "max_jitter_interval",
                "min_jitter_speed",
                "max_jitter_speed"
            ]:
                if hasattr(self.blink_sleep_manager, 'jitter_manager'):
                    print(f"Updating jitter settings: {variable_name}")
                    # Stop current jitter and restart with new settings
                    self.blink_sleep_manager.jitter_manager.stop_all_jitter()
                    self.blink_sleep_manager.jitter_manager.start_jitter_process()

            elif variable_name in ["min_sleep_timeout", "max_sleep_timeout"]:
                if hasattr(self.blink_sleep_manager, 'sleep_manager'):
                    print("Updating sleep timeouts")
                    self.blink_sleep_manager.sleep_manager.on_sleep_timeout_changed()

            elif variable_name in ["min_random_wakeup", "max_random_wakeup"]:
                if hasattr(self.blink_sleep_manager, 'sleep_manager'):
                    print("Updating random wakeup intervals")
                    self.blink_sleep_manager.sleep_manager.on_random_wakeup_changed()

            elif variable_name == "display_off_timeout":
                if hasattr(self.blink_sleep_manager, 'sleep_manager'):
                    print(f"Updating display off timeout to {value} hours")

            elif variable_name in ["stretch_x", "stretch_y", "rotate"]:
                # Force a redraw of the current image to apply new stretching/rotation
                current_img = self.current_filename
                if current_img:
                    print(f"Updating display with new {variable_name}")
                    self.display_image(current_img)

            elif variable_name == "smooth_y":
                print(f"Updating Y-movement smoothing to {value}")
            
            # Log successful update
            print(f"Successfully updated {variable_name} to {value}")
        else:
            print(f"Warning: Unknown setting {variable_name}")

            

if __name__ == "__main__":
    app = QApplication(sys.argv)
    image_folders = ["./eyeballImages/Brown", "./eyeballImages/Blue"]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Initialize and start the PyQt application
    window = FullScreenBlinkApp(image_folders)
    window.start_server_thread('localhost', 65432)

    sys.exit(app.exec_())
