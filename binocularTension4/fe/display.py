import sys
import os
import socket
import threading
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from display_control_panel import DisplayControlPanelWidget  # Import the control panel
from display_live_config import DisplayLiveConfig  # Import LiveConfig for config values
from debug_mode import DebugModeManager  # Import DebugModeManager
from blink_sleep_manager import BlinkSleepManager  # Import the new BlinkSleepManager class
import time
import random
import re  # Import re module for regular expressions

def get_largest_display():
    app = QApplication.instance() or QApplication(sys.argv)
    screens = app.screens()
    largest_screen = max(screens, key=lambda screen: screen.size().width() * screen.size().height())
    return largest_screen

class FullScreenBlinkApp(QWidget):
    update_image_signal = pyqtSignal(str)

    def __init__(self, image_folders):
        super().__init__()
        self.image_folders = {  # Store folders with labels
            "jade": image_folders[0],
            # "gab": image_folders[1],
        }
        self.current_folder = "jade"  # Start with "jade" folder
        self.label = QLabel(self)
        self.filename_label = QLabel(self)
        self.filename_label.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        self.filename_label.setStyleSheet("font-size: 1gpx; color: white; background-color: rgba(0, 0, 0, 0.5); padding: 5px;")
        self.filename_label.setWordWrap(True)
        self.debug_mode_manager = DebugModeManager(self)
        self.setCursor(Qt.BlankCursor)

        self.current_filename = "bt_20_cso.jpg"
        self.update_in_progress = False  # Flag to prevent updates during transitions

        # Load live config values
        self.live_config = DisplayLiveConfig.get_instance()

        # Set up window
        largest_screen = get_largest_display()
        self.move(largest_screen.geometry().x(), largest_screen.geometry().y())
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

        # Load images
        self.image_filenames = {"jade": [], "gab": []}
        self.images = {"jade": {}, "gab": {}}
        self.load_images()

        # Initialize BlinkSleepManager
        self.blink_sleep_manager = BlinkSleepManager(self)

        # Display initial image and set up signal for server updates
        self.display_image(self.current_filename)
        self.update_image_signal.connect(self.update_display_image)

        # Initialize control panel
        self.control_panel = None

    def load_images(self):
        for folder_key, folder_path in self.image_folders.items():
            if os.path.exists(folder_path):
                for filename in os.listdir(folder_path):
                    if filename.endswith(".jpg"):
                        print(filename)
                        image_path = os.path.join(folder_path, filename)
                        pixmap = QPixmap(image_path)
                        self.image_filenames[folder_key].append(filename)
                        self.images[folder_key][filename] = pixmap
        if self.image_filenames["jade"]:  # Start with the first image in "jade"
            self.display_image(self.current_filename)

    def extract_x_from_filename(self, filename):
        """Extract the x value from the filename."""
        match = re.match(r"bt_(\d+)_.*\.jpg", filename)
        if match:
            x_value = int(match.group(1))
            return x_value
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
            self.current_filename = filename  # Update current filename here
        else:
            print(f"Image not found: {image_path}")

    def update_display_image(self, filename):
        if self.blink_sleep_manager.sleep_manager.display_off:
            self.blink_sleep_manager.sleep_manager.display_off = False
            self.blink_sleep_manager.sleep_manager.turn_on_display_()
        if self.update_in_progress:
            print("Update in progress, ignoring new update.")
            return

        # Extract x values from filenames
        current_x = self.extract_x_from_filename(self.current_filename)
        new_x = self.extract_x_from_filename(filename)

        if current_x is not None and new_x is not None:
            delta = abs(new_x - current_x)
            if delta > 5:
                # 50% chance to simulate blink with position change, 50% to do intermediate steps
                if random.random() < 0.8:
                    # Simulate blink with position change
                    print("Simulating blink with position change.")
                    # Prevent updates during blink
                    self.update_in_progress = True
                    # Call simulate_blink with the new filename
                    self.blink_sleep_manager.blink_manager.simulate_blink(new_filename=filename)
                    # Finish update after blink duration
                    blink_speed = self.live_config.blink_speed  # Higher is faster
                    base_delay = 600  # Base delay in ms for the slowest speed
                    total_blink_duration = int((base_delay / blink_speed) * 5)  # 5 steps in simulate_blink
                    QTimer.singleShot(total_blink_duration, lambda: self.finish_update(filename))
                else:
                    # Perform intermediate steps as before
                    print("Performing intermediate steps for large delta.")
                    num_steps = random.randint(2, 4)
                    step_size = (new_x - current_x) / num_steps
                    intermediate_x_values = [int(round(current_x + step_size * i)) for i in range(1, num_steps)]
                    # Ensure x values are within 0-40
                    intermediate_x_values = [max(0, min(40, x)) for x in intermediate_x_values]
                    # Build filenames for intermediate steps
                    rest_of_filename_match = re.match(r"bt_\d+(_.*\.jpg)", filename)
                    if rest_of_filename_match:
                        rest_of_filename = rest_of_filename_match.group(1)
                    else:
                        rest_of_filename = "_cso.jpg"  # Default value if pattern doesn't match
                    # Build a list of filenames
                    intermediate_filenames = [f"bt_{x}{rest_of_filename}" for x in intermediate_x_values]
                    # Set update_in_progress to True
                    self.update_in_progress = True
                    # Schedule the display of intermediate images
                    total_delay = 0
                    for i, intermediate_filename in enumerate(intermediate_filenames):
                        delay_between_steps = random.randint(100, 300)  # Random delay between 100ms and 300ms
                        total_delay += delay_between_steps
                        QTimer.singleShot(total_delay, lambda fn=intermediate_filename: self.display_image(fn))
                    # Finally, after the last intermediate image, display the final image
                    total_delay += random.randint(100, 300)
                    QTimer.singleShot(total_delay, lambda fn=filename: self.display_image(fn))
                    QTimer.singleShot(total_delay, lambda fn=filename: self.finish_update(fn))
                return

        # If no large difference or unable to parse x values, proceed normally
        if self.current_filename != filename:
            self.current_filename = filename
            if self.blink_sleep_manager.sleep_manager.in_sleep_mode:
                print("Exiting sleep mode.")
                self.blink_sleep_manager.sleep_manager.exit_sleep_mode()
            # Update last image time
            if not self.blink_sleep_manager.blink_manager.is_blinking:
                self.display_image(filename)
            self.blink_sleep_manager.update_last_image_time()
            # Check if in sleep mode



    def finish_update(self, filename):
        """Reset the update_in_progress flag after transition."""
        self.update_in_progress = False
        self.current_filename = filename
        print("Finished large jump transition.")

    def switch_image_folder(self, folder_name):
        """
        Switch between the two image folders based on the parameter.
        :param folder_name: "jade" for the first folder, "gab" for the second.
        """
        if folder_name not in self.image_folders:
            print(f"Invalid folder name: {folder_name}. Must be 'jade' or 'gab'.")
            return
        self.current_folder = folder_name
        print(f"Switched to folder: {folder_name}")
        if self.image_filenames[folder_name]:  # Display the first image in the new folder
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
        thread = threading.Thread(target=listen_for_commands, daemon=True)
        thread.start()

    def toggle_control_panel(self):
        """Toggle the control panel visibility."""
        if self.control_panel is None:
            self.control_panel = DisplayControlPanelWidget(self.debug_mode_manager, self)
            self.control_panel.show()
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.BlankCursor)
            self.control_panel.close()
            self.control_panel = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_G:
            self.toggle_control_panel()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    image_folders = ["./eyeballImages/Jade", "./eyeballImages/Gab"]
    window = FullScreenBlinkApp(image_folders)
    window.start_server_thread('localhost', 65432)
    sys.exit(app.exec_())
