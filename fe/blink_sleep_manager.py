from PyQt5.QtCore import QObject
from sleep_manager import SleepManager
from blink_manager import BlinkManager
from jitter_manager import JitterManager
from display_live_config import DisplayLiveConfig
import time


class BlinkSleepManager(QObject):
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.live_config = DisplayLiveConfig.get_instance()
        
        # Track its own last image time
        self.last_image_time = time.time()

        # Initialize managers
        self.sleep_manager = SleepManager(app_instance)
        self.blink_manager = BlinkManager(app_instance, self)
        self.jitter_manager = JitterManager(app_instance, self)

        # Start the jitter process
        self.jitter_manager.start_jitter_process()

    def update_last_image_time(self):
        """Update the last image time for all managers and self."""
        self.last_image_time = time.time()
        self.jitter_manager.update_last_image_time()
        self.sleep_manager.update_last_image_time()
        self.blink_manager.update_last_image_time()

    def get_inactivity_duration(self):
        """Return the duration of inactivity since the last image was updated."""
        return time.time() - self.last_image_time
