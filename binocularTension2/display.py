import sys
import os
import socket
import threading
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QScreen
import random

def get_largest_display():
    app = QApplication.instance() or QApplication(sys.argv)
    # Get all available screens
    screens = app.screens()
    largest_screen = min(screens, key=lambda screen: screen.size().width() * screen.size().height())
    return largest_screen


class FullScreenBlinkApp(QWidget):
    # Define a custom signal to update the image safely from another thread
    update_image_signal = pyqtSignal(str)

    def __init__(self, image_folder):
        super().__init__()
        self.image_folder = image_folder
        self.label = QLabel(self)

        # Initialize with filename 'bt_20_cso.png'
        self.current_filename = "bt_20_cso.png"
        self.is_blinking = False  # Track if a blink cycle is in progress
        self.received_recently = False  # Track if an image was received after a gap of 5+ seconds

        # Get the largest display and set up the full-screen window
        largest_screen = get_largest_display()
        self.move(largest_screen.geometry().x(), largest_screen.geometry().y())

        # Set window flags for full-screen mode
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

        # Initialize a list for storing image filenames and load them
        self.image_filenames = []
        self.images = {}
        self.load_images()

        # Timers for blinking and no image received detection
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.simulate_blink)

        self.no_image_timer = QTimer(self)
        self.no_image_timer.setSingleShot(True)
        self.no_image_timer.timeout.connect(self.start_blinking)

        # Display the initial image (starting at 'bt_20_cso.png')
        self.display_image(self.current_filename)

        # Start the no_image_timer to begin the countdown for blinking after 5 seconds of no image received
        self.no_image_timer.start(5000)  # Start the timer when the app launches

        # Connect the signal to the slot
        self.update_image_signal.connect(self.update_display_image)

    def display_image(self, filename):
        """Display the image based on the given filename."""
        image_path = os.path.join(self.image_folder, filename)
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.label.setPixmap(pixmap)
            self.label.setFixedSize(pixmap.size())
            self.setFixedSize(pixmap.size())
            self.current_filename = filename  # Update current filename
        else:
            print(f"Image not found: {image_path}")

    def load_images(self):
        """Load all images in the folder and store them in a dictionary."""
        for filename in os.listdir(self.image_folder):
            if filename.endswith(".png"):  # Assuming images are in PNG format
                image_path = os.path.join(self.image_folder, filename)
                pixmap = QPixmap(image_path)
                self.image_filenames.append(filename)
                self.images[filename] = pixmap

        # Display the first image once all images are loaded
        if self.image_filenames:
            self.current_filename = self.image_filenames[0]
            self.display_image(self.current_filename)

    def start_blinking(self):
        """Start the blinking cycle if no new image has been received for 5 seconds."""
        self.blink_timer.start(5000)  # Start blinking every 5 seconds

    def stop_blinking(self):
        """Stop the blinking cycle when a new filename is received."""
        self.blink_timer.stop()

    def simulate_blink(self):
        """Simulate blinking sequence."""
        if self.current_filename:
            self.is_blinking = True  # Indicate a blink cycle is in progress
            copy = self.current_filename
            # Modify the third-to-last character of the filename to simulate blinking
            base_filename = self.current_filename[:-7]  # Remove the 'c' and 'o.png'
            blink_filename_f = f"{base_filename}f" + self.current_filename[-6:]  # Change 'c' to 'f'

            # Start blinking sequence (half-open -> closed -> half-open -> open)
            self.display_image(blink_filename_f.replace('o', 'h'))  # Half-open
            QTimer.singleShot(100, lambda: self.display_image(blink_filename_f.replace('o', 'c')))  # Closed
            QTimer.singleShot(300, lambda: self.display_image(blink_filename_f.replace('o', 'h')))  # Half-open
            QTimer.singleShot(400, lambda: self.end_blinking(copy))  # Back to open state

    def end_blinking(self, original_image):
        """End blinking and optionally update to a new image."""
        self.display_image(original_image)
        self.is_blinking = False  # Mark blink cycle as finished

    def start_server_thread(self, host, port):
        """Start a background thread to listen for filename updates."""
        def listen_for_filenames():
            """Background thread to listen for filenames from the server."""
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.bind((host, port))
                server_socket.listen()
                print(f"Server listening on {host}:{port}")

                while True:
                    conn, addr = server_socket.accept()
                    with conn:
                        data = conn.recv(1024).decode()  # Receive the filename
                        if data:
                            print(f"Received filename: {data}")
                            # Emit the signal to update the image in the main thread
                            self.update_image_signal.emit(data)

        # Start the background thread for listening
        thread = threading.Thread(target=listen_for_filenames, daemon=True)
        thread.start()

    def update_display_image(self, filename):
        """Update the displayed image from the server and reset timers."""
        if self.is_blinking:
            # If mid-blink, wait until blink is done before changing the image
            QTimer.singleShot(600, lambda: self.check_and_update_image(filename))
        else:
            self.check_and_update_image(filename)

    def check_and_update_image(self, filename):
        """Update image, check for recent receipt, and handle the 'w' character change."""
        if self.no_image_timer.remainingTime() <= 0 and random.random() < .5:
            # If it's been more than 5 seconds since the last image, change 'o' to 'w'
            filename = filename.replace('o.png', 'w.png')
            self.display_image(filename)
            QTimer.singleShot(3000, lambda: self.display_image(filename.replace('w.png', 'o.png')))  # Revert after 2s
        else:
            # Simply display the new image
            self.display_image(filename)

        # Restart the 5-second timer for detecting image gaps
        self.no_image_timer.start(5000)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Path to the folder with images
    image_folder = "./eyeballImages_738_noise"

    # Initialize and display the full-screen blink app
    window = FullScreenBlinkApp(image_folder)

    # Start the server thread to listen for incoming filenames
    window.start_server_thread('localhost', 65432)

    # Start the application event loop
    sys.exit(app.exec_())
