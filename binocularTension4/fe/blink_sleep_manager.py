import time
import random
from PyQt5.QtCore import QObject, QTimer
from jitter_manager import JitterManager
from sleep_manager import SleepManager
from blink_manager import BlinkManager
from display_live_config import DisplayLiveConfig  # Assuming LiveConfig is accessible


class BlinkSleepManager(QObject):
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.last_image_time = time.time()  # Initialize the last image timestamp

        # Access LiveConfig
        self.live_config = DisplayLiveConfig.get_instance()

        # Initialize managers
        self.sleep_manager = SleepManager(app_instance)
        self.blink_manager = BlinkManager(app_instance, self)
        self.jitter_manager = JitterManager(app_instance, self)

        # Timer for starting jitters after a delay
        self.jitter_start_timer = QTimer(self)
        self.jitter_start_timer.setSingleShot(True)
        self.jitter_start_timer.timeout.connect(self.start_jitter_loop)

        # Timer for jitter loop
        self.jitter_loop_timer = QTimer(self)
        self.jitter_loop_timer.timeout.connect(self.run_jitter)

        # Thresholds
        self.level_1_threshold = self.live_config.jitter_start_delay  # Use jitter start delay from LiveConfig
        self.large_jitter_start_delay = self.live_config.large_jitter_start_delay
        self.current_jitter_level = 0

        # Start the process initially
        self.start_jitter_process()

    def start_jitter_process(self):
        """Start the jitter process with a delay."""
        delay = self.live_config.jitter_start_delay * 1000  # Convert to milliseconds
        self.jitter_start_timer.start(delay)

    def start_jitter_loop(self):
        """Start the jitter loop with randomized intervals."""
        self.update_jitter_level()
        jitter_interval = random.randint(
            self.live_config.min_jitter_interval * 1000, 
            self.live_config.max_jitter_interval * 1000
        )  # Use LiveConfig values for jitter interval
        self.jitter_loop_timer.start(jitter_interval)

    def run_jitter(self):
        """Run the jitter logic based on the current level."""
        self.update_jitter_level()
        self.jitter_manager.simulate_jitter(level=self.current_jitter_level)
        jitter_interval = random.randint(
            self.live_config.min_jitter_interval * 1000, 
            self.live_config.max_jitter_interval * 1000
        )  # Use LiveConfig values for jitter interval
        self.jitter_loop_timer.start(jitter_interval)

    def update_jitter_level(self):
        """Update the jitter level based on inactivity duration."""
        inactivity_duration = time.time() - self.last_image_time
        if inactivity_duration > self.large_jitter_start_delay:
            self.current_jitter_level = 1
        else:
            self.current_jitter_level = 0

    def update_last_image_time(self):
        """Update the timestamp of the last image received and restart the process."""
        self.last_image_time = time.time()
        self.jitter_start_timer.stop()
        self.jitter_loop_timer.stop()
        self.current_jitter_level = 0  # Reset to level 0 on activity
        self.start_jitter_process()  # Restart the process
