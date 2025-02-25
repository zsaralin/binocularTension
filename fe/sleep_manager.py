import random
import time
import os
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from random_wakeup import RandomWakeupManager
from display_controller import get_display_controller

class SleepManager(QObject):
    sleep_mode_entered = pyqtSignal()
    sleep_mode_exited = pyqtSignal()
    display_image_signal = pyqtSignal(str)

    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.in_sleep_mode = False
        self.display_off = False
        self.last_image_time = time.time()
        self.live_config = app_instance.live_config
        self.random_wakeup = RandomWakeupManager(self.app_instance, self)

        self.min_sleep_timeout = self.live_config.min_sleep_timeout * 1000
        self.max_sleep_timeout = self.live_config.max_sleep_timeout * 1000
        self.min_random_wakeup = self.live_config.min_random_wakeup * 1000 
        self.max_random_wakeup = self.live_config.max_random_wakeup * 1000
        self.display_off_timeout_hours = self.live_config.display_off_timeout

        self.sleep_timer = QTimer(self)
        self.sleep_timer.timeout.connect(self.enter_sleep_mode)

        self.random_wakeup_timer = QTimer(self)
        self.random_wakeup_timer.timeout.connect(self.random_wakeup.random_wakeup)

        self.display_off_timer = QTimer(self)
        self.display_off_timer.setSingleShot(True)
        self.display_off_timer.timeout.connect(self.turn_off_display_)

        self.schedule_sleep_timer()

    def schedule_sleep_timer(self):
        """Schedule next sleep timer with random interval."""
        if self.max_sleep_timeout < self.min_sleep_timeout:
            print(f"Warning: max sleep timeout ({self.max_sleep_timeout}ms) is less than min ({self.min_sleep_timeout}ms)")
            # Use min as fallback to prevent errors
            sleep_interval = int(self.min_sleep_timeout)  # Ensure integer
        else:
            # Convert both values to integers for randint
            min_ms = int(self.min_sleep_timeout)
            max_ms = int(self.max_sleep_timeout)
            sleep_interval = random.randint(min_ms, max_ms)
        
        self.sleep_timer.start(sleep_interval)  # sleep_interval is now guaranteed to be int

    def schedule_random_wakeup_timer(self):
        """Schedule random wakeup timer with proper validation and integer conversion."""
        if self.in_sleep_mode:
            if self.max_random_wakeup < self.min_random_wakeup:
                print(f"Warning: max wakeup interval ({self.max_random_wakeup}ms) is less than min ({self.min_random_wakeup}ms)")
                wakeup_interval = int(self.min_random_wakeup)
            else:
                # Convert both values to integers for randint
                min_ms = int(self.min_random_wakeup)
                max_ms = int(self.max_random_wakeup)
                wakeup_interval = random.randint(min_ms, max_ms)
            
            self.random_wakeup_timer.start(wakeup_interval)

    def random_wakeup(self):
        if self.app_instance.debug_mode_manager.debug_mode or self.random_wakeup.in_wakeup or not self.in_sleep_mode:
            return

        print("Starting random wakeup...")
        self.random_wakeup.random_wakeup(self.app_instance)
        self.schedule_random_wakeup_timer()


    def enter_sleep_mode(self):
        if self.in_sleep_mode or self.display_off:
            return

        print("Entering sleep mode...")
        self.in_sleep_mode = True
        self.sleep_mode_entered.emit()
        self.display_sleep_images()
        self.schedule_random_wakeup_timer()
        self.start_display_off_timer()

    def display_sleep_images(self):
        half_closed_eye_filename = self.app_instance.current_filename[:-5] + "h.jpg"
        closed_eye_filename = self.app_instance.current_filename[:-5] + "c.jpg"

        if not os.path.exists(closed_eye_filename):
            closed_eye_filename = closed_eye_filename[:-6] + "sc.jpg"
            if not os.path.exists(closed_eye_filename):
                closed_eye_filename = closed_eye_filename[:-7] + "csc.jpg"

        self.app_instance.display_image(half_closed_eye_filename)
        QTimer.singleShot(100, lambda: self.app_instance.display_image(closed_eye_filename))

    def exit_sleep_mode(self):
        # if self.in_sleep_mode:
        self.in_sleep_mode = False
        print("Exiting sleep mode...")
        self.sleep_timer.stop()  # Stop the current sleep timer to avoid re-triggering
        self.schedule_sleep_timer()
        self.sleep_mode_exited.emit()

    def start_display_off_timer(self):
        timeout_ms = self.display_off_timeout_hours * 3600 * 1000  # Convert hours to milliseconds
        self.display_off_timer.start(timeout_ms) 
        print(f"Display off timer started for {self.display_off_timeout_hours} hours.")

    def turn_off_display_(self):
        # if not self.display_off:
        print("Turning off display...")
        self.sleep_timer.stop()
        self.random_wakeup_timer.stop()
        self.display_off = True
        self.app_instance.display_black_image()

    def turn_on_display_(self):
        print("Turning on display...")
        self.display_off_timer.stop()  # Stop the display off timer
        self.sleep_timer.stop()       # Stop the sleep timer
        self.display_off = False
        self.exit_sleep_mode()


    def update_last_image_time(self):
        self.last_image_time = time.time()
        self.sleep_timer.stop()
        self.random_wakeup_timer.stop()
        self.display_off_timer.stop()
        self.schedule_sleep_timer()

    def on_sleep_timeout_changed(self):
        """
        Update sleep timeouts when settings change.
        Converts from seconds in live_config to milliseconds for internal use.
        """
        # Convert to milliseconds and ensure integer values
        self.min_sleep_timeout = int(self.live_config.min_sleep_timeout * 1000)
        self.max_sleep_timeout = int(self.live_config.max_sleep_timeout * 1000)
        self.schedule_sleep_timer()

    def on_random_wakeup_changed(self):
        """
        Update random wakeup intervals when settings change.
        Converts from seconds in live_config to milliseconds for internal use.
        """
        # Convert to milliseconds and ensure integer values
        self.min_random_wakeup = int(self.live_config.min_random_wakeup * 1000)
        self.max_random_wakeup = int(self.live_config.max_random_wakeup * 1000)
        
        if self.in_sleep_mode:
            self.schedule_random_wakeup_timer()
