import sys
import os
import socket
import threading
import time
import random
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from display_control_panel import DisplayControlPanelWidget  # Import the control panel
from display_live_config import DisplayLiveConfig  # Import LiveConfig for config values

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
        self.debug_mode = False
        self.current_filename = "bt_20_cso.png"
        self.is_blinking = False
        self.in_sleep_mode = False
        self.last_image_time = time.time()  # Initialize timestamp for no-image check
        self.last_displayed_image = None

        # Load live config values
        self.live_config = DisplayLiveConfig.get_instance()
        self.min_blink_interval = self.live_config.min_blink_interval
        self.max_blink_interval = self.live_config.max_blink_interval
        self.sleep_timeout = self.live_config.sleep_duration * 1000 * 60
        self.inactivity_time_interval = self.live_config.inactivity_timer  

        # Set up window
        largest_screen = get_largest_display()
        self.move(largest_screen.geometry().x(), largest_screen.geometry().y())
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

        # Load images
        self.image_filenames = []
        self.images = {}
        self.load_images()

        # Timers for inactivity, continuous blinking, and sleep mode
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.check_inactivity)
        self.reset_inactivity_timer()

        self.continuous_blink_timer = QTimer(self)
        self.continuous_blink_timer.timeout.connect(self.simulate_blink)

        self.sleep_timer = QTimer(self)
        self.sleep_timer.timeout.connect(self.enter_sleep_mode)
        self.sleep_timer.start(self.sleep_timeout)

        # Display initial image and set up signal for server updates
        self.display_image(self.current_filename)
        self.update_image_signal.connect(self.update_display_image)

        # Initialize control panel
        self.control_panel = None

    def load_images(self):
        for filename in os.listdir(self.image_folder):
            if filename.endswith(".png"):
                image_path = os.path.join(self.image_folder, filename)
                pixmap = QPixmap(image_path)
                self.image_filenames.append(filename)
                self.images[filename] = pixmap
        if self.image_filenames:
            self.current_filename = self.image_filenames[0]
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
            self.current_filename = filename
        else:
            print(f"Image not found: {image_path}")

    def reset_inactivity_timer(self):
        """Resets the inactivity timer with a new randomized interval."""
        self.inactivity_timer.start(500)

    def check_inactivity(self):
        """Checks if enough time has passed since the last image update to start blinking."""
        if time.time() - self.last_image_time > self.inactivity_time_interval:
            self.start_continuous_blinking()
    def start_continuous_blinking(self):
        """Start repeated blinking if no image is received for an extended period."""
        if not self.in_sleep_mode and not self.is_blinking:
            self.inactivity_timer.stop()  # Stop inactivity timer to prevent multiple triggers
            self.simulate_blink()  # Start the blinking cycle

    def stop_continuous_blinking(self):
        """Stop continuous blinking and reset inactivity timer."""
        self.continuous_blink_timer.stop()
        self.reset_inactivity_timer()

    def schedule_next_blink(self):
        """Schedule the next blink with a randomized interval between min and max intervals."""
        if not self.in_sleep_mode:
            next_blink_interval = random.randint(self.min_blink_interval, self.max_blink_interval)
            self.continuous_blink_timer.start(next_blink_interval)
            print(f"Next blink scheduled in {next_blink_interval} ms")

    def enter_sleep_mode(self):
        """Enter sleep mode and display half-closed eye briefly before fully closing."""
        if self.is_blinking:
            print("Waiting for blink to finish before entering sleep mode.")
            QTimer.singleShot(100, self.enter_sleep_mode)  # Check again shortly
            return

        self.in_sleep_mode = True
        self.stop_continuous_blinking()  # Ensure blinking is fully stopped

        # Define filenames for half-closed and fully closed images
        half_closed_eye_filename = self.current_filename.replace('o', 'h')
        closed_eye_filename = self.current_filename.replace('o', 'c')

        # Display half-closed eye briefly
        self.display_image(half_closed_eye_filename)
        print("Displaying half-closed eye")

        # After a brief delay, display the fully closed eye
        QTimer.singleShot(200, lambda: self.display_image(closed_eye_filename))
        print("Entering sleep mode with closed eye after half-closed")
    def simulate_blink(self):
        """Simulate the blink by toggling images if not in sleep mode, debug mode, or already blinking."""
        if self.in_sleep_mode or self.debug_mode or self.is_blinking:
            print("Blinking skipped: in sleep mode, debug mode, or already blinking")
            return  # Do not blink if in sleep mode, debug mode, or already blinking

        self.is_blinking = True
        original_filename = self.current_filename

        # Construct filenames for half-closed and closed images
        half_closed_eye_filename = self.current_filename[:-5] + "h.png"
        closed_eye_filename = self.current_filename[:-5] + "c.png"

        # Replace third-last character with 'f' for blinking images
        half_closed_eye_filename = half_closed_eye_filename[:-7] + "f" + half_closed_eye_filename[-6:]
        closed_eye_filename = closed_eye_filename[:-7] + "f" + closed_eye_filename[-6:]

        print(f"Starting blink sequence with original image: {original_filename}")
        print(f"Half-closed eye filename: {half_closed_eye_filename}")
        print(f"Closed eye filename: {closed_eye_filename}")

        # Start the blink sequence
        self.display_image(half_closed_eye_filename)
        print("Displayed half-closed eye")

        QTimer.singleShot(100, lambda: (self.display_image(closed_eye_filename), print("Displayed closed eye")))
        QTimer.singleShot(300, lambda: (self.display_image(half_closed_eye_filename), print("Displayed half-closed eye again")))
        QTimer.singleShot(400, lambda: self.end_blinking(original_filename))

    def enter_sleep_mode(self):
        """Enter sleep mode and display half-closed eye briefly before fully closing."""
        if self.is_blinking:
            print("Waiting for blink to finish before entering sleep mode.")
            QTimer.singleShot(100, self.enter_sleep_mode)  # Check again shortly
            return

        self.in_sleep_mode = True
        self.stop_continuous_blinking()  # Ensure blinking is fully stopped

        # Define filenames for half-closed and fully closed images with 'f' as the third-last character
        half_closed_eye_filename = self.current_filename[:-5] + "h.png"
        closed_eye_filename = self.current_filename[:-5] + "c.png"

        # Replace third-last character with 'f' for the sleep mode half-closed and closed states
        half_closed_eye_filename = half_closed_eye_filename[:-7] + "f" + half_closed_eye_filename[-6:]
        closed_eye_filename = closed_eye_filename[:-7] + "f" + closed_eye_filename[-6:]

        # Display half-closed eye briefly
        self.display_image(half_closed_eye_filename)
        print("Displaying half-closed eye")

        # After a brief delay, display the fully closed eye
        QTimer.singleShot(200, lambda: self.display_image(closed_eye_filename))
        print("Entering sleep mode with closed eye after half-closed")

    def end_blinking(self, original_image):
        """End the blinking effect and reset the eye to the original state."""
        self.display_image(original_image)
        print(f"Blinking ended, returned to original image: {original_image}")
        self.is_blinking = False  # Reset the blinking flag
        self.schedule_next_blink()  # Schedule the next blink after the current one ends


    def on_blink_interval_changed(self, value):
        """Update the blink interval in live config and restart the inactivity timer."""
        self.min_blink_interval = self.live_config.min_blink_interval
        self.max_blink_interval = self.live_config.max_blink_interval
        self.reset_inactivity_timer()

    def on_sleep_timeout_changed(self, value):
        """Update the sleep timeout in live config."""
        self.sleep_timeout = self.live_config.sleep_duration * 1000 * 60
        self.sleep_timer.start(self.sleep_timeout)

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
                        if data and not self.debug_mode:  # Only update if not in debug mode
                            self.update_image_signal.emit(data)
        thread = threading.Thread(target=listen_for_filenames, daemon=True)
        thread.start()

    def exit_sleep_mode(self):
            """Exit sleep mode if data received and reset timers."""
            if self.in_sleep_mode:
                print("Exiting sleep mode.")
                self.in_sleep_mode = False
                self.reset_inactivity_timer()
                self.sleep_timer.start(self.sleep_timeout)


    def update_display_image(self, filename):
        """Update the display image, exit sleep mode if active, and reset timers."""
        self.exit_sleep_mode()  # Exit sleep mode if active
        if not self.is_blinking:
            self.check_and_update_image(filename)

    def check_and_update_image(self, filename):
        if filename != self.current_filename:
            if random.random() < 0.5 and time.time() - self.last_image_time > 5:  # Check if 5 seconds have passed
                filename = self.current_filename.replace('o.png', 'w.png')
                self.display_image(filename)
                QTimer.singleShot(3000, lambda: self.display_image(filename.replace('w.png', 'o.png')))
            else:
                self.display_image(filename)
            self.last_image_time = time.time()  # Reset timestamp on image update
            self.stop_continuous_blinking()  # Stop blinking if a new image is received
            self.reset_inactivity_timer()    # Reset inactivity timer

    def toggle_debug_mode(self):
        self.debug_mode = not self.debug_mode
        print(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_G:
            self.toggle_control_panel()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    image_folder = "./eyeballImages/201"
    window = FullScreenBlinkApp(image_folder)
    window.start_server_thread('localhost', 65432)
    sys.exit(app.exec_())
