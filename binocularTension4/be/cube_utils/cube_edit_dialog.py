from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QFormLayout, QSlider, QLabel, QDialogButtonBox, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt

class CubeEditDialog(QDialog):
    def __init__(self, cube_manager, parent=None):
        super(CubeEditDialog, self).__init__(parent)
        self.cube_manager = cube_manager
        self.current_cube_id = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Edit Cubes")
        self.setFixedSize(600, 400)  # Set a fixed width and reduce height

        layout = QVBoxLayout(self)

        # Cube list
        self.cube_list = QListWidget()
        self.cube_list.setFixedHeight(100)
        for cube_id in self.cube_manager.cubes:
            self.cube_list.addItem(f"Cube {cube_id}")
        self.cube_list.currentTextChanged.connect(self.load_cube)
        layout.addWidget(self.cube_list)

        # Buttons for adding and deleting cubes
        button_layout = QHBoxLayout()
        add_cube_button = QPushButton("Add Cube")
        add_cube_button.clicked.connect(self.add_cube)
        button_layout.addWidget(add_cube_button)

        delete_cube_button = QPushButton("Delete Cube")
        delete_cube_button.clicked.connect(self.delete_cube)
        button_layout.addWidget(delete_cube_button)
        layout.addLayout(button_layout)

        # Sliders for cube properties with decimal steps
        self.slider_layout = QFormLayout()

        # Position, size, and depth sliders
        self.x_slider = self.create_slider("X", -10, 10, 0.1)
        self.y_slider = self.create_slider("Y", -10, 10, 0.1)
        self.z_slider = self.create_slider("Z", -10, 10, 0.1)
        self.width_slider = self.create_slider("Width", 0.1, 10, 0.1)
        self.height_slider = self.create_slider("Height", 0.1, 10, 0.1)
        self.depth_slider = self.create_slider("Depth", 0.1, 10, 0.1)

        # Rotation sliders
        self.rotation_x_slider = self.create_slider("Rotate X", 0, 360, 1)
        self.rotation_y_slider = self.create_slider("Rotate Y", 0, 360, 1)
        self.rotation_z_slider = self.create_slider("Rotate Z", 0, 360, 1)

        layout.addLayout(self.slider_layout)

        # Save and Close buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_changes)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def create_slider(self, label, min_val, max_val, step):
        """Helper to create a labeled slider with decimal steps."""
        slider_layout = QHBoxLayout()
        slider_label = QLabel(label)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(min_val / step))
        slider.setMaximum(int(max_val / step))
        slider.setValue(0)
        slider.setSingleStep(1)
        value_label = QLabel(f"{0:.1f}")
        value_label.setFixedWidth(40)  # Set fixed width for alignment

        # Connect slider to update the cube and label dynamically
        slider.valueChanged.connect(lambda value: value_label.setText(f"{value * step:.1f}"))
        slider.valueChanged.connect(lambda value: self.update_current_cube())

        # Add label, slider, and value label on the same row
        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(slider)
        slider_layout.addWidget(value_label)
        self.slider_layout.addRow(slider_layout)
        return slider

    def add_cube(self):
        """Add a new cube with default values to the CubeManager's cubes dictionary."""
        new_id = str(len(self.cube_manager.cubes))
        default_cube = {"x": 0, "y": 0, "z": -5, "width": 1, "height": 1, "depth": 1, "rotation_x": 0, "rotation_y": 0, "rotation_z": 0}

        # Add the cube to the manager and update the list
        self.cube_manager.cubes[new_id] = default_cube
        new_item = f"Cube {new_id}"
        self.cube_list.addItem(new_item)
        self.cube_list.setCurrentItem(self.cube_list.findItems(new_item, Qt.MatchExactly)[0])

    def delete_cube(self):
        """Delete the selected cube from the CubeManager's cubes dictionary."""
        selected_item = self.cube_list.currentItem()
        if selected_item:
            cube_id = selected_item.text().split(" ")[1]
            del self.cube_manager.cubes[cube_id]
            self.cube_list.takeItem(self.cube_list.row(selected_item))
            self.current_cube_id = None
            # Clear sliders after deletion
            self.x_slider.setValue(0)
            self.y_slider.setValue(0)
            self.z_slider.setValue(0)
            self.width_slider.setValue(10)
            self.height_slider.setValue(10)
            self.depth_slider.setValue(10)
            self.rotation_x_slider.setValue(0)
            self.rotation_y_slider.setValue(0)
            self.rotation_z_slider.setValue(0)

    def load_cube(self, cube_id):
        """Load selected cube's values into sliders"""
        if not cube_id:
            return
        self.current_cube_id = cube_id.split(" ")[1]
        cube = self.cube_manager.cubes[self.current_cube_id]
        
        # Set slider values based on cube properties
        self.x_slider.setValue(int(cube["x"] / 0.1))
        self.y_slider.setValue(int(cube["y"] / 0.1))
        self.z_slider.setValue(int(cube["z"] / 0.1))
        self.width_slider.setValue(int(cube["width"] / 0.1))
        self.height_slider.setValue(int(cube["height"] / 0.1))
        self.depth_slider.setValue(int(cube["depth"] / 0.1))
        self.rotation_x_slider.setValue(int(cube["rotation_x"]))
        self.rotation_y_slider.setValue(int(cube["rotation_y"]))
        self.rotation_z_slider.setValue(int(cube["rotation_z"]))

    def update_current_cube(self):
        """Update the current cube's data with slider values, applying scaling for decimal steps"""
        if self.current_cube_id:
            self.cube_manager.cubes[self.current_cube_id] = {
                "x": self.x_slider.value() * 0.1,
                "y": self.y_slider.value() * 0.1,
                "z": self.z_slider.value() * 0.1,
                "width": self.width_slider.value() * 0.1,
                "height": self.height_slider.value() * 0.1,
                "depth": self.depth_slider.value() * 0.1,
                "rotation_x": self.rotation_x_slider.value(),
                "rotation_y": self.rotation_y_slider.value(),
                "rotation_z": self.rotation_z_slider.value()
            }

    def save_changes(self):
        """Save cubes to JSON and close dialog"""
        self.cube_manager.save_cubes()
        self.accept()
