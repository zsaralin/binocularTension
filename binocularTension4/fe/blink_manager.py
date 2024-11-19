import os
import random
from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class BlinkManager(QObject):
    blink_started = pyqtSignal()
    blink_ended = pyqtSignal()

    def __init__(self, main_app, blink_sleep_manager):
        super().__init__()
        self.main_app = main_app
        self.is_blinking = False
        self.blink_sleep_manager = blink_sleep_manager
        # Load live config for blink intervals
        self.live_config = self.main_app.live_config
        self.min_blink_interval = self.live_config.min_blink_interval
        self.max_blink_interval = self.live_config.max_blink_interval
        # Initialize the blink timer
        self.continuous_blink_timer = QTimer(self)
        self.continuous_blink_timer.timeout.connect(self.simulate_blink)

        self.schedule_next_blink()


    def schedule_next_blink(self):
        """Schedule the next blink if not in sleep mode."""
        if self.blink_sleep_manager.sleep_manager.in_sleep_mode:
            print("Not scheduling blink: in sleep mode.")
            self.continuous_blink_timer.stop()  # Stop timer if in sleep mode
            return

        next_blink_interval = random.randint(self.min_blink_interval, self.max_blink_interval) * 1000
        self.continuous_blink_timer.start(next_blink_interval)
        print(f"Next blink scheduled in {next_blink_interval // 1000} seconds")

    def simulate_blink(self):
        """
        Simulate the blink by toggling images with variable speed based on blink speed.
        """
        if self.blink_sleep_manager.sleep_manager.in_sleep_mode or self.main_app.debug_mode_manager.debug_mode or self.is_blinking:
            print("Blinking skipped: in sleep mode, debug mode, or already blinking")
            return

        # Get the blink speed from a slider (assume the range is 1-10, where 10 is fastest)
        blink_speed = self.main_app.live_config.blink_speed  # Higher is faster
        base_delay = 600  # Base delay in ms for the slowest speed

        # Calculate the delay per step (invert blink speed to reduce delay)
        step_delay = int(base_delay / blink_speed)  # e.g., speed 10 -> 60ms, speed 1 -> 600ms

        self.is_blinking = True
        self.blink_started.emit()
        current_filename = self.main_app.current_filename

        half_closed_eye_filename = current_filename[:-5] + "h.jpg"
        closed_eye_filename = current_filename[:-5] + "c.jpg"

        if not os.path.exists(closed_eye_filename):
            closed_eye_filename = closed_eye_filename[:-6] + "sc.jpg"  # Try "sc.jpg" first
            if not os.path.exists(closed_eye_filename):
                closed_eye_filename = closed_eye_filename[:-7] + "csc.jpg"  # Fallback to "csc.jpg"

        def display_image_if_not_in_sleep(filename):
            if not self.blink_sleep_manager.sleep_manager.in_sleep_mode:
                self.main_app.display_image(filename)
            else:
                print(f"Skipping image display ({filename}) due to sleep mode.")

        # Adjust timing dynamically based on calculated step delay
        QTimer.singleShot(step_delay, lambda: display_image_if_not_in_sleep(half_closed_eye_filename))
        QTimer.singleShot(step_delay * 2, lambda: display_image_if_not_in_sleep(closed_eye_filename))
        QTimer.singleShot(step_delay * 3, lambda: display_image_if_not_in_sleep(half_closed_eye_filename))
        QTimer.singleShot(step_delay * 4, lambda: self.end_blinking(current_filename))
    def end_blinking(self, original_filename):
        """End the blinking effect and reset the eye to the original state."""
        if not self.blink_sleep_manager.sleep_manager.in_sleep_mode:
            self.main_app.display_image(original_filename)
            print(f"Blinking ended, returned to original image: {original_filename}")
            self.is_blinking = False
            self.blink_ended.emit()
            self.schedule_next_blink()

    def on_blink_interval_changed(self, value):
        """Update the blink interval in live config and restart the blink timer."""
        self.min_blink_interval = self.live_config.min_blink_interval
        self.max_blink_interval = self.live_config.max_blink_interval
        self.schedule_next_blink()

