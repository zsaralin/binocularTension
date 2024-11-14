import json
import os

class DisplayLiveConfig:
    _instance = None

    def __init__(self):
        # Load default values and update with config.json if available
        self.config_file = "display_config.json"
        self.min_sleep_timeout = 1          # Default in mins
        self.max_sleep_timeout = 3          # Default in mins
        self.min_random_wakeup = 1          # Default in mins
        self.max_random_wakeup = 3          # Default in mins
        self.min_blink_interval = 1000      # Default minimum blink interval in milliseconds
        self.max_blink_interval = 5000      # Default maximum blink interval in milliseconds
        self.inactivity_timer = 2           # Default inactivity timer in seconds
        self.display_off_timeout = 5        # Default display off timeout in seconds
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
                self.inactivity_timer = config_data.get("inactivity_timer", self.inactivity_timer)
                self.display_off_timeout = config_data.get("display_off_timeout", self.display_off_timeout)

    def save_config(self):
        """Save the current configuration to the file."""
        config_data = {
            "min_sleep_timeout": self.min_sleep_timeout,
            "max_sleep_timeout": self.max_sleep_timeout,
            "min_random_wakeup": self.min_random_wakeup,
            "max_random_wakeup": self.max_random_wakeup,
            "min_blink_interval": self.min_blink_interval,
            "max_blink_interval": self.max_blink_interval,
            "inactivity_timer": self.inactivity_timer,
            "display_off_timeout": self.display_off_timeout
        }
        with open(self.config_file, 'w') as file:
            json.dump(config_data, file, indent=4)

    def update_duration(self, min_sleep_timeout=None, max_sleep_timeout=None, min_blink_interval=None,
                        max_blink_interval=None, inactivity_timer=None, min_random_wakeup=None,
                        max_random_wakeup=None, display_off_timeout=None):
        """Update the durations and save to config."""
        if min_sleep_timeout is not None:
            self.min_sleep_timeout = min_sleep_timeout
        if max_sleep_timeout is not None:
            self.max_sleep_timeout = max_sleep_timeout
        if min_blink_interval is not None:
            self.min_blink_interval = min_blink_interval
        if max_blink_interval is not None:
            self.max_blink_interval = max_blink_interval
        if inactivity_timer is not None:
            self.inactivity_timer = inactivity_timer
        if min_random_wakeup is not None:
            self.min_random_wakeup = min_random_wakeup
        if max_random_wakeup is not None:
            self.max_random_wakeup = max_random_wakeup
        if display_off_timeout is not None:
            self.display_off_timeout = display_off_timeout
        self.save_config()
