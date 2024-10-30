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
    screens = app.screens()
    largest_screen = min(screens, key=lambda screen: screen.size().width() * screen.size().height())
    return largest_screen

class FullScreenBlinkApp(QWidget):
    update_image_signal = pyqtSignal(str)

    def __init__(self, image_folder):
        super().__init__()
        self.image_folder = image_folder
        self.label = QLabel(self)
        self.debug_mode = False  # Debug mode flag
        self.current_filename = "bt_20_cso.png"
        self.is_blinking = False
        self.received_recently = False

        largest_screen = get_largest_display()
        self.move(largest_screen.geometry().x(), largest_screen.geometry().y())
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()

        self.image_filenames = []
        self.images = {}
        self.load_images()

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.simulate_blink)

        self.no_image_timer = QTimer(self)
        self.no_image_timer.setSingleShot(True)
        self.no_image_timer.timeout.connect(self.start_blinking)

        self.display_image(self.current_filename)
        self.no_image_timer.start(5000)

        self.update_image_signal.connect(self.update_display_image)

    def display_image(self, filename):
        image_path = os.path.join(self.image_folder, filename)
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.label.setPixmap(pixmap)
            self.label.setFixedSize(pixmap.size())
            self.setFixedSize(pixmap.size())
            self.current_filename = filename
        else:
            print(f"Image not found: {image_path}")

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

    def start_blinking(self):
        self.blink_timer.start(5000)

    def stop_blinking(self):
        self.blink_timer.stop()

    def simulate_blink(self):
        if self.current_filename and self.debug_mode:
            self.is_blinking = True
            copy = self.current_filename
            base_filename = self.current_filename[:-7]
            blink_filename_f = f"{base_filename}f" + self.current_filename[-6:]

            self.display_image(blink_filename_f.replace('o', 'h'))
            QTimer.singleShot(100, lambda: self.display_image(blink_filename_f.replace('o', 'c')))
            QTimer.singleShot(300, lambda: self.display_image(blink_filename_f.replace('o', 'h')))
            QTimer.singleShot(400, lambda: self.end_blinking(copy))

    def end_blinking(self, original_image):
        self.display_image(original_image)
        self.is_blinking = False

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

    def update_display_image(self, filename):
        if self.is_blinking:
            QTimer.singleShot(600, lambda: self.check_and_update_image(filename))
        else:
            self.check_and_update_image(filename)

    def check_and_update_image(self, filename):
        if self.no_image_timer.remainingTime() <= 0 and random.random() < .5:
            filename = filename.replace('o.png', 'w.png')
            self.display_image(filename)
            QTimer.singleShot(3000, lambda: self.display_image(filename.replace('w.png', 'o.png')))
        else:
            self.display_image(filename)
        self.no_image_timer.start(5000)

    def toggle_debug_mode(self):
        self.debug_mode = not self.debug_mode
        print(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_D:
            self.toggle_debug_mode()
        elif self.debug_mode:
            base, xpos, depth, ypos, mode = self.parse_filename()
            xpos = int(xpos)
            if event.key() == Qt.Key_Left:
                xpos = max(xpos - 1, 0)
            elif event.key() == Qt.Key_Right:
                xpos = min(xpos + 1, 201)
            elif event.key() == Qt.Key_Up:
                # Logic for 'up' key to update ypos
                if ypos == 's':
                    ypos = 'u'
                elif ypos == 'd':
                    ypos = 's'
            elif event.key() == Qt.Key_Down:
                # Logic for 'down' key to update ypos
                if ypos == 's':
                    ypos = 'd'
                elif ypos == 'u':
                    ypos = 's'
            elif event.key() == Qt.Key_Space:
                depth = 'f' if depth == 'c' else 'c'
            elif event.key() == Qt.Key_O:
                mode = 'o'
            elif event.key() == Qt.Key_C:
                mode = 'c'
            elif event.key() == Qt.Key_W:
                mode = 'w'

            # Update the filename with potentially modified values
            self.update_filename(base, xpos, depth, ypos, mode)

    def parse_filename(self):
        parts = self.current_filename.split('_')
        base = parts[0]
        xpos = parts[1].zfill(2)  # Zero-padding for xpos
        depth_ypos_mode = parts[2].split('.')[0]
        depth = depth_ypos_mode[0] if depth_ypos_mode[0] in 'ocw' else 'f'  # Default depth if invalid
        ypos = depth_ypos_mode[1] if len(depth_ypos_mode) > 1 else 's'  # Default ypos if missing
        mode = depth_ypos_mode[2] if len(depth_ypos_mode) > 2 else 'o'  # Default mode if missing
        return base, xpos, depth, ypos, mode

    def update_filename(self, base, xpos, depth, ypos, mode):
        # Format xpos with zero-padding for consistent filenames
        new_filename = f"{base}_{xpos}_{depth}{ypos}{mode}.png"
        print(new_filename)
        if new_filename in self.images:
            self.display_image(new_filename)    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    image_folder = "./eyeballImages/201"
    window = FullScreenBlinkApp(image_folder)
    window.start_server_thread('localhost', 65432)
    sys.exit(app.exec_())
