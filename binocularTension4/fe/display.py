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
from turnoff_display import turn_on_display  # Assuming `turnoff_display.py` has `turn_on_display`

def get_largest_display():
    app = QApplication.instance() or QApplication(sys.argv)
    screens = app.screens()
    largest_screen = min(screens, key=lambda screen: screen.size().width() * screen.size().height())
    return largest_screen

class FullScreenBlinkApp(QWidget):
    update_image_signal = pyqtSignal(str)

    def __init__(self, image_folder):
        super().__init__()
        self.image_folder = image_folder
        self.label = QLabel(self)
        self.filename_label = QLabel(self)
        self.filename_label.setAlignment(Qt.AlignTop | Qt.AlignCenter)
        self.filename_label.setStyleSheet("font-size: 24px; color: white; background-color: rgba(0, 0, 0, 0.5); padding: 5px;")
        self.filename_label.setWordWrap(True)
        self.debug_mode_manager = DebugModeManager(self)

        self.current_filename = "bt_20_cso.jpg"

        # Load live config values
        self.live_config = DisplayLiveConfig.get_instance()

        # Set up window
        largest_screen = get_largest_display()
        self.move(largest_screen.geometry().x(), largest_screen.geometry().y())
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

        # Load images
        self.image_filenames = []
        self.images = {}
        self.load_images()

        # Initialize BlinkSleepManager
        self.blink_sleep_manager = BlinkSleepManager(self)
        self.blink_sleep_manager.display_image_signal.connect(self.display_image)

        # Display initial image and set up signal for server updates
        self.display_image(self.current_filename)
        self.update_image_signal.connect(self.update_display_image)

        # Initialize control panel
        self.control_panel = None

    def load_images(self):
        for filename in os.listdir(self.image_folder):
            if filename.endswith(".jpg"):
                image_path = os.path.join(self.image_folder, filename)
                pixmap = QPixmap(image_path)
                self.image_filenames.append(filename)
                self.images[filename] = pixmap
        if self.image_filenames:
            self.current_filename = "bt_20_cso.jpg"
            self.display_image(self.current_filename)

    def display_image(self, filename):
        image_path = os.path.join(self.image_folder, filename)
        if os.path.exists(image_path):
            pixmap = self.images.get(filename)
            if not pixmap:
                pixmap = QPixmap(image_path)
                self.images[filename] = pixmap
            self.label.setPixmap(pixmap)
            self.label.setFixedSize(pixmap.size())
            self.setFixedSize(pixmap.size())
            self.filename_label.setText(filename)
            self.filename_label.adjustSize()
            self.current_filename = filename
        else:
            print(f"Image not found: {image_path}")

    def update_display_image(self, filename): 
        """Update the display image, exit sleep mode if active, and reset timers."""
        
        # Exit sleep mode if active
        self.blink_sleep_manager.exit_sleep_mode()
        
        # Turn the display back on if it was turned off
        if self.blink_sleep_manager.display_off:
            # Call the function to turn on the display
            turn_on_display()
            # Reset display_off flag to indicate display is now on
            self.blink_sleep_manager.display_off = False
        
        # Proceed with updating the image if not blinking or in wakeup
        if not self.blink_sleep_manager.is_blinking and not self.blink_sleep_manager.in_wakeup:
            self.check_and_update_image(filename)

    def check_and_update_image(self, filename):
        if filename != self.current_filename:
            self.display_image(filename)
            self.blink_sleep_manager.update_last_image_time()
            self.blink_sleep_manager.stop_continuous_blinking()
            self.blink_sleep_manager.reset_inactivity_timer()

    def start_server_thread(self, host, port):
        def listen_for_filenames():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.bind((host, port))
                server_socket.listen()
                print(f"Server listening on {host}:{port}")
                while True:
                    conn, addr = server_socket.accept()
                    with conn:
                        data = conn.recv(1024).decode()
                        if data and not self.debug_mode_manager.debug_mode:
                            self.update_image_signal.emit(data)
        thread = threading.Thread(target=listen_for_filenames, daemon=True)
        thread.start()

    def toggle_control_panel(self):
        """Toggle the control panel visibility."""
        if self.control_panel is None:
            self.control_panel = DisplayControlPanelWidget(self.debug_mode_manager)
            self.control_panel.show()
        else:
            self.control_panel.close()
            self.control_panel = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_G:
            self.toggle_control_panel()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    image_folder = "./eyeballImages/V1"
    window = FullScreenBlinkApp(image_folder)
    window.start_server_thread('localhost', 65432)
    sys.exit(app.exec_())
