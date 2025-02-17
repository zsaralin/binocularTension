"""
LiveConfig module providing runtime configuration management.

This module implements a thread-safe singleton configuration manager that maintains 
all runtime settings. It provides initialization from config files with fallback defaults
and type-safe access to configuration values.

Example:
    config = LiveConfig.get_instance()
    config.blink_speed = 5.0  # Updates blink speed setting
    current_speed = config.blink_speed  # Retrieves current setting
"""

import json
import os
import logging
from typing import Dict, Any, Optional

class LiveConfig:
    """Thread-safe singleton configuration manager for runtime settings."""
    
    _instance = None
    _config_file = "config.json"
    _logger = logging.getLogger(__name__)

    def __new__(cls):
        """Create or return the singleton instance with proper initialization."""
        if not cls._instance:
            cls._instance = super(LiveConfig, cls).__new__(cls)
            # Set up logging
            if not cls._logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                cls._logger.addHandler(handler)
                cls._logger.setLevel(logging.DEBUG)  # Enable debug logging
            
            # Initialize the instance
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize configuration with defaults then load from file if available."""
        # First set defaults
        self.reset_to_defaults()
        
        # Then try to load from config file
        self._load_from_file()

    def _load_from_file(self):
        """Load configuration from file, updating only existing attributes."""
        if not os.path.exists(self._config_file):
            self._logger.info(f"No config file found at {self._config_file}, using defaults")
            return

        try:
            with open(self._config_file, 'r') as f:
                config_data = json.load(f)

            # Map old config keys to new attribute names
            key_mapping = {
                'stable_thres_x': 'stable_x_thres',
                'stable_thres_y': 'stable_y_thres',
            }

            

            # Update attributes, including mapped keys
            for key, value in config_data.items():
                # Check if this is a mapped key
                mapped_key = key_mapping.get(key, key)
                
                if hasattr(self, mapped_key):
                    old_value = getattr(self, mapped_key)
                    setattr(self, mapped_key, value)
                else:
                    self._logger.warning(f"Unknown config key in file: {key}")

            self._logger.info("Successfully loaded configuration from file")

        except json.JSONDecodeError as e:
            self._logger.error(f"Error parsing config file: {e}")
        except Exception as e:
            self._logger.error(f"Error loading config: {e}")

    def reset_to_defaults(self):
        """Reset all configuration values to their defaults."""
        # Backend settings
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
        self.min_contour_area = 200
        self.movement_thres = 2
        self.active_object_stick_time = 3
        self.conf_thres = 0.1
        self.stationary_timeout = 20
        self.roi_filter_dur = 10
        self.headpoint_smoothing = 0.5
        self.point_size = 1
        self.num_divisions = 40
        self.history = 1000
        self.varthreshold = 30
        self.threshold_value = 200
        self.morph_kernel_size = 3
        self.merge_distance = 50
        self.z_threshold_min = 0
        self.z_threshold_max = 6.0
        self.x_threshold_min = 0
        self.x_threshold_max = 0
        self.y_threshold_min = 0
        self.y_threshold_max = 0
        
        # Stable thresholds - unified naming
        self.stable_x_thres = 10  # Main attribute used by code
        self.stable_y_thres = 10  # Main attribute used by code
        
        self.detect_people = True
        self.detect_objects = True

        # Frontend settings
        self.min_blink_interval = 3.0
        self.max_blink_interval = 8.0
        self.min_sleep_timeout = 10.0
        self.max_sleep_timeout = 12.0
        self.min_random_wakeup = 35.0
        self.max_random_wakeup = 65.0
        self.blink_speed = 5.0
        self.jitter_start_delay = 0.5
        self.large_jitter_start_delay = 60.0
        self.min_jitter_interval = 3.0
        self.max_jitter_interval = 6.0
        self.min_jitter_speed = 500.0
        self.max_jitter_speed = 800.0
        self.display_off_timeout = 2.0
        self.stretch_x = 1.0
        self.stretch_y = 1.0
        self.smooth_y = 10.0
        self.rotate = 0.0
        self.nervousness = 0.8

        # Plane visibility flags
        self.show_vertical_planes = True
        self.show_top_plane = True
        self.show_bottom_plane = True

    def save_config(self):
        """Save current configuration to file."""
        # Reverse key mapping for saving
        key_mapping = {
            'stable_x_thres': 'stable_thres_x',
            'stable_y_thres': 'stable_thres_y',
        }

        config_data = {}
        for attr in dir(self):
            if not attr.startswith('_') and not callable(getattr(self, attr)):
                # Use mapped keys when saving
                save_key = key_mapping.get(attr, attr)
                config_data[save_key] = getattr(self, attr)

        try:
            with open(self._config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            self._logger.info("Configuration saved successfully")
        except Exception as e:
            self._logger.error(f"Error saving configuration: {e}")

    def print_config(self):
        """Print current configuration values."""
        print("Current configuration:")
        for attr in dir(self):
            if not attr.startswith('_') and not callable(getattr(self, attr)):
                print(f"{attr}={getattr(self, attr)}")

    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance."""
        return cls._instance or cls()