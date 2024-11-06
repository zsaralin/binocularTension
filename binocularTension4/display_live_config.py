import json
import os

class DisplayLiveConfig:
    _instance = None

    def __init__(self):
        # Load default values and update with config.json if available
        self.config_file = "display_config.json"
        self.sleep_duration = 3       # Default value in mins (3 minutes)
        self.min_blink_interval = 1000     # Default minimum blink interval in milliseconds
        self.max_blink_interval = 5000     # Default maximum blink interval in milliseconds
        self.inactivity_timer = 2
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
                self.sleep_duration = config_data.get("sleep_duration", self.sleep_duration)
                self.min_blink_interval = config_data.get("min_blink_interval", self.min_blink_interval)
                self.max_blink_interval = config_data.get("max_blink_interval", self.max_blink_interval)
                self.inactivity_timer = config_data.get("inactivity_timer", self.inactivity_timer)

    def save_config(self):
        """Save the current configuration to the file."""
        config_data = {
            "sleep_duration": self.sleep_duration,
            "min_blink_interval": self.min_blink_interval,
            "max_blink_interval": self.max_blink_interval,
            "inactivity_timer": self.inactivity_timer
        }
        with open(self.config_file, 'w') as file:
            json.dump(config_data, file, indent=4)

    def update_duration(self, sleep_duration=None, min_blink_interval=None, max_blink_interval=None, inactivity_timer = None):
        """Update the durations and save to config."""
        if sleep_duration is not None:
            self.sleep_duration = sleep_duration
        if min_blink_interval is not None:
            self.min_blink_interval = min_blink_interval
        if max_blink_interval is not None:
            self.max_blink_interval = max_blink_interval
        if inactivity_timer is not None:
            self.inactivity_timer = inactivity_timer
        self.save_config()
