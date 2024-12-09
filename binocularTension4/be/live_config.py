# live_config.py
class LiveConfig:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(LiveConfig, cls).__new__(cls)
            # Initialize live values with defaults
            cls._instance.reset_to_defaults()
        return cls._instance

    def reset_to_defaults(self):
        self.version = "Jade"
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
        self.movement_thres = 5  # Default threshold for person movement
        self.headpoint_smoothing = 0.5
        self.tracking_hold_duration = 5
        self.extended_timeout = 2
        self.always_closest = True
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
        self.stable_x_thres = 0
        self.stable_y_thres = 0
        self.stable_z_thres = 0
        self.detect_people = True
        self.detect_objects = True
    # Accessor for the singleton instance
    @classmethod
    def get_instance(cls):
        return cls._instance or cls()
