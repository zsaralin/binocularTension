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
        self.rotate_x = 0
        self.rotate_y = 0
        self.rotate_z = 0
        self.translate_x = 0
        self.translate_y = 0
        self.translate_z = 0
        self.y_top_divider = 0
        self.y_bottom_divider = 0
        self.x_divider_angle = 0
        self.z_divider = 0
        self.z_divider_curve = 0
        self.draw_planes = True
        self.min_contour_area = 500  # Default for minimum contour area
        self.person_movement_thres = 0.01  # Default threshold for person movement
        self.point_size = 1  # Default threshold for person movement
        self.num_divisions= 40
        self.z_threshold_min= 0
        self.z_threshold_max= 6.0
        self.x_threshold_min= 0
        self.x_threshold_max= 0
        self.y_threshold_min= 0
        self.y_threshold_max= 0


    # Accessor for the singleton instance
    @classmethod
    def get_instance(cls):
        return cls._instance or cls()
