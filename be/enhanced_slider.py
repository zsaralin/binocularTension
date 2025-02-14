"""
Enhanced slider widget with precise float value handling.

This module provides a QSlider subclass that maintains float precision
while still using integer positions internally for the UI.

Example:
    slider = EnhancedSlider(Qt.Horizontal, decimals=2)
    slider.set_value_programmatically(15.75)
"""

from PyQt5.QtWidgets import QSlider
from PyQt5.QtCore import Qt
from control_panel_update_mixin import ProgrammaticUpdateMixin

class EnhancedSlider(QSlider, ProgrammaticUpdateMixin):
    """
    Enhanced slider that maintains float precision.
    
    This class extends QSlider to handle float values precisely while
    still using integer positions for the UI slider component.
    
    Attributes:
        decimals (int): Number of decimal places to maintain
        _scale_factor (int): Internal scaling factor for float-to-int conversion
        _real_value (float): Current actual float value
    """

    def __init__(self, *args, decimals=2, **kwargs):
        """
        Initialize enhanced slider with float precision support.
        
        Args:
            *args: Positional arguments for QSlider
            decimals (int): Number of decimal places to maintain
            **kwargs: Keyword arguments for QSlider
        """
        super().__init__(*args, **kwargs)
        self.init_update_tracking()
        self.decimals = decimals
        self._scale_factor = 10 ** decimals
        self._real_value = 0.0

    def set_float_range(self, min_val: float, max_val: float):
        """
        Set the range using float values.
        
        Args:
            min_val (float): Minimum value
            max_val (float): Maximum value
        """
        super().setRange(
            int(min_val * self._scale_factor),
            int(max_val * self._scale_factor)
        )

    def set_float_value(self, value: float):
        """
        Set the slider position using a float value.
        
        Args:
            value (float): Value to set
        """
        self._real_value = value
        super().setValue(int(value * self._scale_factor))

    def get_float_value(self) -> float:
        """
        Get the current value as a float.
        
        Returns:
            float: Current slider value
        """
        return self._real_value

    def set_value_programmatically(self, value: float):
        """
        Set a float value without triggering change handlers.
        
        Args:
            value (float): Value to set
        """
        try:
            self._is_programmatic_update = True
            self.set_float_value(value)
        finally:
            self._is_programmatic_update = False