import os
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PIL import Image

class EyeWidget(QWidget):
    _instance = None  # Class-level attribute to store the singleton instance

    def __new__(cls, *args, **kwargs):
        # Check if an instance already exists; if so, return it
        if cls._instance is None:
            cls._instance = super(EyeWidget, cls).__new__(cls)
        return cls._instance

    def __init__(self, parent=None):
        super(EyeWidget, self).__init__(parent)
        
        if not hasattr(self, 'initialized'):  # Initialize only once
            self.initialized = True
            self.image_folder = "../fe/eyeballImages/Female"

            # Set up QLabel to display images
            self.label = QLabel(self)
            self.label.setAlignment(Qt.AlignCenter)

            # Main layout
            layout = QVBoxLayout()
            layout.addWidget(self.label)
            self.setLayout(layout)

            # Load and display the first image by default
            self.display_first_image()

    def display_first_image(self):
        """Load and display the first image found in the image folder."""
        image_files = [f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        
        if image_files:
            first_image = image_files[0]
            self.load_image(first_image)
        else:
            print("No images found in the folder.")

    def load_image(self, filename):
        """Load and display an image from the image folder by filename."""
        file_path = os.path.join(self.image_folder, filename)
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return
        
        with Image.open(file_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')

            data = img.tobytes("raw", "RGB")
            q_image = QImage(data, img.width, img.height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.label.setPixmap(pixmap.scaled(
                self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))

    def resizeEvent(self, event):
        """Handle resizing to maintain aspect ratio of displayed image."""
        if self.label.pixmap():
            self.label.setPixmap(self.label.pixmap().scaled(
                self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        super(EyeWidget, self).resizeEvent(event)
