import json
import os

class DisplayLiveConfig:
    _instance = None

    def __init__(self):
        # Load default values and update with config.json if available
        self.config_file = "display_config.json"
        self.min_sleep_timeout = 30          # Default in mins
        self.max_sleep_timeout = 180         # Default in mins
        self.min_random_wakeup = 30          # Default in mins
        self.max_random_wakeup = 180         # Default in mins
        self.min_blink_interval = 3          # Default minimum blink interval in seconds
        self.max_blink_interval = 8          # Default maximum blink interval in seconds
        self.display_off_timeout = 5         # Default display off timeout in seconds
        self.stretch_x = 1
        self.stretch_y = 1
        self.rotate = 0
        self.smooth_y = 5
        self.nervousness = 0.5               # Default nervousness level (0 to 1)
        self.blink_speed = 5                 # Default blink speed (range: 1 - 10, higher is faster)
        self.jitter_start_delay = 2          # Default delay before jitters start (seconds)
        self.large_jitter_start_delay = 5    # Default delay for large jitter pattern (seconds)
        self.min_jitter_interval = 3         # Default minimum jitter interval (seconds)
        self.max_jitter_interval = 6         # Default maximum jitter interval (seconds)
        self.min_jitter_speed = 1            # Default minimum jitter speed (range: 1 - 10)
        self.max_jitter_speed = 10           # Default maximum jitter speed (range: 1 - 10)
        self.load_config()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DisplayLiveConfig()
        return cls._instance

    def load_config(self):
        """Load configuration from file if it exists."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                config_data = json.load(file)
                self.min_sleep_timeout = config_data.get("min_sleep_timeout", self.min_sleep_timeout)
                self.max_sleep_timeout = config_data.get("max_sleep_timeout", self.max_sleep_timeout)
                self.min_random_wakeup = config_data.get("min_random_wakeup", self.min_random_wakeup)
                self.max_random_wakeup = config_data.get("max_random_wakeup", self.max_random_wakeup)
                self.min_blink_interval = config_data.get("min_blink_interval", self.min_blink_interval)
                self.max_blink_interval = config_data.get("max_blink_interval", self.max_blink_interval)
                self.display_off_timeout = config_data.get("display_off_timeout", self.display_off_timeout)
                self.stretch_x = config_data.get("stretch_x", self.stretch_x)
                self.stretch_y = config_data.get("stretch_y", self.stretch_y)
                self.rotate = config_data.get("rotate", self.rotate)
                self.smooth_y = config_data.get("smooth_y", self.smooth_y)

                self.nervousness = config_data.get("nervousness", self.nervousness)
                self.blink_speed = config_data.get("blink_speed", self.blink_speed)
                self.jitter_start_delay = config_data.get("jitter_start_delay", self.jitter_start_delay)
                self.large_jitter_start_delay = config_data.get("large_jitter_start_delay", self.large_jitter_start_delay)
                self.min_jitter_interval = config_data.get("min_jitter_interval", self.min_jitter_interval)
                self.max_jitter_interval = config_data.get("max_jitter_interval", self.max_jitter_interval)
                self.min_jitter_speed = config_data.get("min_jitter_speed", self.min_jitter_speed)
                self.max_jitter_speed = config_data.get("max_jitter_speed", self.max_jitter_speed)

    def save_config(self):
        """Save the current configuration to the file."""
        config_data = {
            "min_sleep_timeout": self.min_sleep_timeout,
            "max_sleep_timeout": self.max_sleep_timeout,
            "min_random_wakeup": self.min_random_wakeup,
            "max_random_wakeup": self.max_random_wakeup,
            "min_blink_interval": self.min_blink_interval,
            "max_blink_interval": self.max_blink_interval,
            "display_off_timeout": self.display_off_timeout,
            "stretch_x": self.stretch_x,
            "stretch_y": self.stretch_y,
            "smooth_y": self.smooth_y,
            "rotate": self.rotate,
            "nervousness": self.nervousness,
            "blink_speed": self.blink_speed,
            "jitter_start_delay": self.jitter_start_delay,
            "large_jitter_start_delay": self.large_jitter_start_delay,
            "min_jitter_interval": self.min_jitter_interval,
            "max_jitter_interval": self.max_jitter_interval,
            "min_jitter_speed": self.min_jitter_speed,
            "max_jitter_speed": self.max_jitter_speed,
        }

        # Try to preserve existing version selector settings
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    existing_config = json.load(f)
                    # Preserve version selector settings
                    for key in ['selected_folder', 'auto_switch_enabled', 
                            'auto_switch_interval_low', 'auto_switch_interval_high']:
                        if key in existing_config:
                            config_data[key] = existing_config[key]
        except Exception as e:
            print(f"Warning: Could not preserve existing version settings: {e}")

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            print("Configuration saved successfully")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def update_duration(self, min_sleep_timeout=None, max_sleep_timeout=None, min_blink_interval=None,
                        max_blink_interval=None, min_random_wakeup=None, max_random_wakeup=None,
                        display_off_timeout=None, nervousness=None, blink_speed=None,
                        jitter_start_delay=None, large_jitter_start_delay=None,
                        min_jitter_interval=None, max_jitter_interval=None,
                        min_jitter_speed=None, max_jitter_speed=None):
        """Update the durations and save to config."""
        if min_sleep_timeout is not None:
            self.min_sleep_timeout = min_sleep_timeout
        if max_sleep_timeout is not None:
            self.max_sleep_timeout = max_sleep_timeout
        if min_blink_interval is not None:
            self.min_blink_interval = min_blink_interval
        if max_blink_interval is not None:
            self.max_blink_interval = max_blink_interval
        if min_random_wakeup is not None:
            self.min_random_wakeup = min_random_wakeup
        if max_random_wakeup is not None:
            self.max_random_wakeup = max_random_wakeup
        if display_off_timeout is not None:
            self.display_off_timeout = display_off_timeout
        if nervousness is not None:
            self.nervousness = nervousness
        if blink_speed is not None:
            self.blink_speed = blink_speed
        if jitter_start_delay is not None:
            self.jitter_start_delay = jitter_start_delay
        if large_jitter_start_delay is not None:
            self.large_jitter_start_delay = large_jitter_start_delay
        if min_jitter_interval is not None:
            self.min_jitter_interval = min_jitter_interval
        if max_jitter_interval is not None:
            self.max_jitter_interval = max_jitter_interval
        if min_jitter_speed is not None:
            self.min_jitter_speed = min_jitter_speed
        if max_jitter_speed is not None:
            self.max_jitter_speed = max_jitter_speed
        self.save_config()
