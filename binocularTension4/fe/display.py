import sys
import os
import socket
import threading
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from display_control_panel import DisplayControlPanelWidget  # Import the control panel
from display_live_config import DisplayLiveConfig  # Import LiveConfig for config values
from debug_mode import DebugModeManager  # Import DebugModeManager
from blink_sleep_manager import BlinkSleepManager  # Import the new BlinkSleepManager class
import time
import random
from PyQt5.QtCore import  QTimer
def get_largest_display():
    app = QApplication.instance() or QApplication(sys.argv)
    screens = app.screens()
    largest_screen = min(screens, key=lambda screen: screen.size().width() * screen.size().height())
    return largest_screen

class FullScreenBlinkApp(QWidget):
    update_image_signal = pyqtSignal(str)

    def __init__(self, image_folders):
        super().__init__()
        self.image_folders = {  # Store folders with labels
            "jade": image_folders[0],
            "gab": image_folders[1],
        }
        self.current_folder = "jade"  # Start with "jade" folder
        self.label = QLabel(self)
        self.filename_label = QLabel(self)
        self.filename_label.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        self.filename_label.setStyleSheet("font-size: 24px; color: white; background-color: rgba(0, 0, 0, 0.5); padding: 5px;")
        self.filename_label.setWordWrap(True)
        self.debug_mode_manager = DebugModeManager(self)
        self.setCursor(Qt.BlankCursor)

        self.current_filename = "bt_20_cso.jpg"

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
        # self.blink_sleep_manager.last_image_time_updated.connect(self.display_image)

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
                        image_path = os.path.join(folder_path, filename)
                        pixmap = QPixmap(image_path)
                        self.image_filenames[folder_key].append(filename)
                        self.images[folder_key][filename] = pixmap
        if self.image_filenames["jade"]:  # Start with the first image in "jade"
            self.display_image(self.current_filename)

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
            # self.current_filename = filename
        else:
            print(f"Image not found: {image_path}")

    def update_display_image(self, filename):
        # Check if the display is off
        if self.blink_sleep_manager.sleep_manager.display_off:
            self.blink_sleep_manager.sleep_manager.display_off = False
            self.blink_sleep_manager.sleep_manager.turn_on_display_()
        if self.current_filename != filename : 
            self.current_filename = filename
            
            # Update last image time
            self.blink_sleep_manager.update_last_image_time()
            
            # Check if in sleep mode
            if self.blink_sleep_manager.sleep_manager.in_sleep_mode:
                print("Exiting sleep mode.")
                self.blink_sleep_manager.sleep_manager.exit_sleep_mode()
            
            # Check if blinking or wakeup is in progress
            # if not self.blink_sleep_manager.blink_manager.is_blinking and not self.blink_sleep_manager.sleep_manager.in_wakeup:
            current_time = time.time()
            inactivity_duration = current_time - self.blink_sleep_manager.last_image_time
            
            # Random wake effect logic
            if inactivity_duration > 5 and random.random() < 0.2:  # 20% chance
                # Generate the "w.jpg" filename
                wake_filename = filename[:-5] + "w.jpg"
                
                # Display the "w.jpg" version for 300ms, then the regular "o.jpg" version
                self.display_image(wake_filename)  # Show wake image immediately
                
                QTimer.singleShot(300, lambda: self.display_image(filename))  # Switch to regular image
                return
            else:
                self.display_image(filename)  # Show regular image
    
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
