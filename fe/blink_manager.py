import os
import random
import time
from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class BlinkManager(QObject):
    blink_started = pyqtSignal()
    blink_ended = pyqtSignal()

    def __init__(self, main_app, blink_sleep_manager):
        super().__init__()
        self.main_app = main_app
        self.is_blinking = False
        self.blink_sleep_manager = blink_sleep_manager
        self.last_image_time = time.time()  # Initialize the last image received time
        # Load live config for blink intervals
        self.live_config = self.main_app.live_config
        self.min_blink_interval = self.live_config.min_blink_interval
        self.max_blink_interval = self.live_config.max_blink_interval

        # Initialize timers
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self.handle_inactivity)

        self.blink_timer = QTimer(self)
        self.blink_timer.setSingleShot(True)
        self.blink_timer.timeout.connect(self.simulate_blink)

        self.check_inactivity()

    def check_inactivity(self):
        """Start checking for inactivity."""
        self.inactivity_timer.start(500)  # Check for 1 second of inactivity

    def handle_inactivity(self):
        """Handle 1 second of inactivity by blinkmating immediately."""
        if time.time() - self.last_image_time >= random.randint(1, 3) and not self.is_blinking:  # Confirm 1 second of inactivity
            self.simulate_blink()  # Blink immediately
        else:
            self.check_inactivity()

    def simulate_blink(self, new_filename=None):
        if self.blink_sleep_manager.sleep_manager.in_sleep_mode or self.main_app.debug_mode_manager.debug_mode or self.is_blinking or (new_filename is None and self.main_app.update_in_progress):
            print("Blinking skipped: in sleep mode, debug mode, or already blinking")
            return

        # Get the blink speed from LiveConfig (assumed to be in the range 1-10)
        blink_speed = self.main_app.live_config.blink_speed  # Higher is faster
        base_delay = 600  # Base delay in ms for the slowest speed

        # Calculate the delay per step (invert blink speed to reduce delay)
        step_delay = int(base_delay / blink_speed)  # e.g., speed 10 -> 60ms, speed 1 -> 600ms
        self.is_blinking = True
        self.blink_started.emit()
        current_filename = self.main_app.current_filename

        # Extract the base filename (without the eye state suffix)
        base_filename = current_filename[:-5]  # Remove the last 5 characters (e.g., 'o.jpg')

        half_closed_eye_filename = base_filename + "h.jpg"
        closed_eye_filename = base_filename + "c.jpg"

        # Handle missing closed eye images
        if not os.path.exists(closed_eye_filename):
            closed_eye_filename = closed_eye_filename[:-6] + "sc.jpg"  # Try "sc.jpg" first
            if not os.path.exists(closed_eye_filename):
                closed_eye_filename = closed_eye_filename[:-7] + "csc.jpg"  # Fallback to "csc.jpg"

        def display_image_if_not_in_sleep(filename):
            if not self.blink_sleep_manager.sleep_manager.in_sleep_mode:
                self.main_app.display_image(filename)
            else:
                print(f"Skipping image display ({filename}) due to sleep mode.")

        if new_filename and new_filename != current_filename:
            # Blink with position change
            new_base_filename = new_filename[:-5]  # Remove the last 5 characters from new_filename
            new_open_eye_filename = new_filename
            new_half_closed_eye_filename = new_base_filename + "h.jpg"
            new_closed_eye_filename = new_base_filename + "c.jpg"

            # Handle missing closed eye images for new position
            if not os.path.exists(new_closed_eye_filename):
                new_closed_eye_filename = new_closed_eye_filename[:-6] + "sc.jpg"  # Try "sc.jpg" first
                if not os.path.exists(new_closed_eye_filename):
                    new_closed_eye_filename = new_closed_eye_filename[:-7] + "csc.jpg"  # Fallback to "csc.jpg"

            # Sequence:
            # 1. Half-closed eye at current position
            # 2. Closed eye at current position
            # 3. Closed eye at new position
            # 4. Half-closed eye at new position
            # 5. Open eye at new position
            QTimer.singleShot(step_delay, lambda: display_image_if_not_in_sleep(half_closed_eye_filename))
            QTimer.singleShot(step_delay * 2, lambda: display_image_if_not_in_sleep(closed_eye_filename))
            QTimer.singleShot(step_delay * 3, lambda: display_image_if_not_in_sleep(new_closed_eye_filename))
            QTimer.singleShot(step_delay * 4, lambda: display_image_if_not_in_sleep(new_half_closed_eye_filename))
            QTimer.singleShot(step_delay * 5, lambda: self.end_blinking(new_open_eye_filename))
        else:
            # Regular blink in the same position
            # Sequence:
            # 1. Half-closed eye at current position
            # 2. Closed eye at current position
            # 3. Half-closed eye at current position
            # 4. Open eye at current position
            QTimer.singleShot(step_delay, lambda: display_image_if_not_in_sleep(half_closed_eye_filename))
            QTimer.singleShot(step_delay * 2, lambda: display_image_if_not_in_sleep(closed_eye_filename))
            QTimer.singleShot(step_delay * 3, lambda: display_image_if_not_in_sleep(half_closed_eye_filename))
            QTimer.singleShot(step_delay * 4, lambda: self.end_blinking(current_filename))

    def end_blinking(self, original_filename):
        """End the blinking effect and set the next interval."""
        # if not self.blink_sleep_manager.sleep_manager.in_sleep_mode:
        self.main_app.display_image(original_filename)
        self.is_blinking = False
        self.blink_ended.emit()

        # Schedule the next random blink interval
        random_interval = random.randint(self.min_blink_interval, self.max_blink_interval) * 1000
        self.blink_timer.start(random_interval)

    def update_last_image_time(self):
        """Update the last image time and reset blink logic."""
        self.last_image_time = time.time()
        # if self.is_blinking:
        #     print("Blink interrupted by image update.")
        #     self.is_blinking = False
        self.inactivity_timer.stop()
        self.blink_timer.stop()
        self.check_inactivity()

    def on_blink_interval_changed(self):
        """Update the blink interval in live config and restart the blink timer."""
        self.min_blink_interval = self.live_config.min_blink_interval
        self.max_blink_interval = self.live_config.max_blink_interval
        self.check_inactivity()
