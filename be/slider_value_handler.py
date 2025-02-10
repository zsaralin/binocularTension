# slider_value_handler.py

class SliderValueHandler:
    """
    Handler for converting between slider integer values and actual decimal values.
    
    This class manages the conversion between integer slider positions and their 
    corresponding real values, handling different step sizes appropriately.
    
    @brief Handles conversion and scaling of slider values
    """
    
    @staticmethod
    def get_scale_factor(step: float) -> int:
        """
        Determine the scale factor based on step size.
        
        @param step: The step size for the slider
        @return: Scale factor to convert between slider and actual values
        """
        if step >= 1:
            return 1
        elif step == 0.1:
            return 10
        elif step == 0.01:
            return 100
        return 1

    @staticmethod
    def to_slider_value(actual_value: float, step: float) -> int:
        """
        Convert an actual value to a slider position.
        
        @param actual_value: The real value to convert
        @param step: The step size for the slider
        @return: Integer value for slider position
        """
        scale_factor = SliderValueHandler.get_scale_factor(step)
        if step >= 1:
            # For whole numbers, round to nearest step
            return int(round(actual_value / step) * step)
        else:
            # For decimals, scale up to slider resolution
            return int(actual_value * scale_factor)

    @staticmethod
    def from_slider_value(slider_value: int, step: float) -> float:
        """
        Convert a slider position to its actual value.
        
        @param slider_value: The slider position value
        @param step: The step size for the slider
        @return: Actual float value
        """
        scale_factor = SliderValueHandler.get_scale_factor(step)
        if step >= 1:
            # For whole numbers, ensure step alignment
            return float(round(slider_value / step) * step)
        else:
            # For decimals, scale down to actual value
            return slider_value / scale_factor

    @staticmethod
    def format_display_value(value: float, step: float) -> str:
        """
        Format a value for display based on step size.
        
        @param value: The value to format
        @param step: The step size for the slider
        @return: Formatted string representation
        """
        if step >= 1:
            return f"{int(value)}"
        elif step == 0.1:
            return f"{value:.1f}"
        elif step == 0.01:
            return f"{value:.2f}"
        return f"{value:.2f}"