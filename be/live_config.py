# # live_config.py
# class LiveConfig:
#     _instance = None

#     def __new__(cls):
#         if not cls._instance:
#             cls._instance = super(LiveConfig, cls).__new__(cls)
#             # Initialize live values with defaults
#             cls._instance.reset_to_defaults()
#         return cls._instance

#     def reset_to_defaults(self):
#         self.version = "Brown"
#         self.rotate_x = 0
#         self.rotate_y = 0
#         self.rotate_z = 0
#         self.translate_x = 0
#         self.translate_y = 0
#         self.translate_z = 0
#         self.camera_z = 0
#         self.y_top_divider = 0
#         self.y_top_divider_angle = 0
#         self.y_bottom_divider = 0
#         self.y_bottom_divider_angle = 0
#         self.x_divider_angle = 0
#         self.draw_planes = True
#         self.min_contour_area = 200  # Default for minimum contour area
#         self.movement_thres = 2  # Default threshold for person movement
#         self.active_object_stick_time = 3,
#         self.conf_thres = 0.1,
#         self.stationary_timeout = 20,
#         self.roi_filter_dur = 10, 
#         self.headpoint_smoothing = 0.5
#         self.point_size = 1
#         self.num_divisions = 40
#         self.history = 1000  # Background subtractor history
#         self.varthreshold = 30  # Background subtractor variance threshold
#         self.threshold_value = 200  # Threshold for binary mask
#         self.morph_kernel_size = 3  # Morphological kernel size
#         self.merge_distance = 50  # Distance for merging boxes
#         self.z_threshold_min = 0
#         self.z_threshold_max = 6.0
#         self.x_threshold_min = 0
#         self.x_threshold_max = 0
#         self.y_threshold_min = 0
#         self.y_threshold_max = 0
#         self.stable_x_thres = 0
#         self.stable_y_thres = 0
#         self.detect_people = True
#         self.detect_objects = True

#         # Plane visibility flags
#         self.show_vertical_planes = True
#         self.show_top_plane = True
#         self.show_bottom_plane = True

        
#     # Accessor for the singleton instance
#     @classmethod
#     def get_instance(cls):
#         return cls._instance or cls()


"""
LiveConfig module providing runtime configuration management for binocular tension system.

This module implements a thread-safe singleton configuration manager that maintains
all runtime settings for the display and tracking system. It provides type-safe
access to configuration values with validation.

Example:
    config = LiveConfig.get_instance()
    config.blink_speed = 5.0  # Updates blink speed setting
    current_speed = config.blink_speed  # Retrieves current setting
"""

# live_config.py

class LiveConfig:
    """
    Thread-safe singleton configuration manager for runtime settings.
    
    Maintains a single instance of configuration parameters used throughout
    the binocular tension system. Provides default values and ensures
    consistency across all components.
    """
    
    _instance = None

    def __new__(cls):
        """
        Create or return the singleton instance.
        
        Returns:
            LiveConfig: The singleton configuration instance
        """
        if not cls._instance:
            cls._instance = super(LiveConfig, cls).__new__(cls)
            # Initialize live values with defaults
            cls._instance.reset_to_defaults()
        return cls._instance

    def reset_to_defaults(self):
        """Reset all configuration values to their defaults."""
        self.version = "Female"
        self.rotate_x = 0
        self.rotate_y = 0
        self.rotate_z = 0
        self.translate_x = 0
        self.translate_y = 0
        self.translate_z = 0
        self.camera_z = 0
        self.y_top_divider = 0
        self.y_top_divider_angle = 0
        self.y_bottom_divider = 0
        self.y_bottom_divider_angle = 0
        self.x_divider_angle = 0
        self.draw_planes = True
        self.min_contour_area = 200  # Default for minimum contour area
        self.movement_thres = 2  # Default threshold for person movement
        self.active_object_stick_time = 3
        self.conf_thres = 0.1
        self.stationary_timeout = 20
        self.roi_filter_dur = 10
        self.headpoint_smoothing = 0.5
        self.point_size = 1
        self.num_divisions = 40
        self.history = 1000  # Background subtractor history
        self.varthreshold = 30  # Background subtractor variance threshold
        self.threshold_value = 200  # Threshold for binary mask
        self.morph_kernel_size = 3  # Morphological kernel size
        self.merge_distance = 50  # Distance for merging boxes
        self.z_threshold_min = 0
        self.z_threshold_max = 6.0
        self.x_threshold_min = 0
        self.x_threshold_max = 0
        self.y_threshold_min = 0
        self.y_threshold_max = 0
        # Changed from float to int for deque maxlen
        self.stable_x_thres = 10  # Integer value for deque maxlen
        self.stable_y_thres = 10  # Integer value for deque maxlen
        self.detect_people = True
        self.detect_objects = True

        # Plane visibility flags
        self.show_vertical_planes = True
        self.show_top_plane = True
        self.show_bottom_plane = True
        
    @classmethod
    def get_instance(cls):
        """
        Get or create the singleton instance.
        
        Returns:
            LiveConfig: The singleton configuration instance
        """
        return cls._instance or cls()