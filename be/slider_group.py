"""Base slider group implementation for control panels."""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QSlider, QLineEdit
from PyQt5.QtCore import Qt

class SliderGroup(QWidget):
    """
    Base class for slider groups with label, slider, and numeric input.
    
    Attributes:
        label_text (str): Text label for the slider
        min_val (float): Minimum allowed value
        max_val (float): Maximum allowed value
        step (float): Step size for the slider
    """
    
    def __init__(self, label_text: str, initial_value: float,
                 min_val: float, max_val: float, step: float, parent=None):
        super().__init__(parent)

        self.label_text = label_text
        self.min_val = min_val
        self.max_val = max_val
        self.step = step

        layout = QHBoxLayout(self)

        # Label
        self.label_widget = QLabel(label_text, self)
        layout.addWidget(self.label_widget)

        # Slider
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(int(min_val / step), int(max_val / step))
        self.slider.setValue(int(initial_value / step))
        layout.addWidget(self.slider)

        # Value display label
        self.value_label = QLabel(f"{initial_value:.1f}", self)
        self.value_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.value_label)

        # Numeric input field
        self.line_edit = QLineEdit(f"{initial_value:.1f}", self)
        self.line_edit.setFixedWidth(50)
        self.line_edit.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.line_edit)

        # Connect signals
        self.slider.valueChanged.connect(self.on_slider_changed)
        self.line_edit.textChanged.connect(self.on_text_changed)

    def on_slider_changed(self, slider_pos: float):
        new_val = slider_pos * self.step
        self.value_label.setText(f"{new_val:.1f}")
        self.line_edit.setText(f"{new_val:.1f}")

    def on_text_changed(self, text: str):
        try:
            typed_val = float(text)
            typed_val = max(min(typed_val, self.max_val), self.min_val)
            slider_pos = int(typed_val / self.step)
            self.slider.setValue(slider_pos)
        except ValueError:
            pass

    def set_value(self, new_val: float):
        new_val = max(min(new_val, self.max_val), self.min_val)
        slider_pos = int(new_val / self.step)
        self.slider.setValue(slider_pos)

    def current_value(self) -> float:
        return float(self.line_edit.text())