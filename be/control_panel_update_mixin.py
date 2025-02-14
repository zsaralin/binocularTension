"""
Mixin class providing safe update mechanisms for control panel components.

This mixin prevents feedback loops when updating UI components by temporarily
disabling change handlers during programmatic updates.

Example:
    class MySlider(QSlider, ProgrammaticUpdateMixin):
        def __init__(self):
            super().__init__()
            self.init_update_tracking()
"""

from PyQt5.QtCore import QObject

class ProgrammaticUpdateMixin(QObject):
    """
    Mixin that adds safe programmatic update capabilities to UI components.
    
    This mixin provides mechanisms to temporarily disable change handlers
    during programmatic updates to prevent feedback loops.
    """

    def init_update_tracking(self):
        """Initialize the programmatic update tracking state."""
        self._is_programmatic_update = False

    def set_value_programmatically(self, value):
        """
        Set a value without triggering change handlers.
        
        Args:
            value: The value to set
        """
        try:
            self._is_programmatic_update = True
            self.setValue(value)
        finally:
            self._is_programmatic_update = False

    @property 
    def is_programmatic_update(self):
        """Check if current update is programmatic.
        
        Returns:
            bool: True if update is programmatic, False otherwise
        """
        return getattr(self, '_is_programmatic_update', False)