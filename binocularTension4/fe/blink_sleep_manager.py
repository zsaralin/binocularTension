import random
import time
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
# Import the turn_off_display function from turnoff_display.py
from turnoff_display import turn_off_display, turn_on_display
class BlinkSleepManager(QObject):
    display_image_signal = pyqtSignal(str)
    blink_started = pyqtSignal()
    blink_ended = pyqtSignal()
    sleep_mode_entered = pyqtSignal()
    sleep_mode_exited = pyqtSignal()

    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.is_blinking = False
        self.display_off = False
        self.in_sleep_mode = False
        self.in_wakeup = False
        self.last_image_time = time.time()
        self.live_config = app_instance.live_config
        self.min_blink_interval = self.live_config.min_blink_interval
        self.max_blink_interval = self.live_config.max_blink_interval
        self.min_sleep_timeout = self.live_config.min_sleep_timeout * 500 * 60
        self.max_sleep_timeout = self.live_config.max_sleep_timeout * 500 * 60
        self.min_random_wakeup = self.live_config.min_random_wakeup * 1000 * 60
        self.max_random_wakeup = self.live_config.max_random_wakeup * 1000 * 60
        self.inactivity_time_interval = self.live_config.inactivity_timer
        self.display_off_timeout_hours = self.live_config.display_off_timeout

        # Timers
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.check_inactivity)
        self.reset_inactivity_timer()

        self.continuous_blink_timer = QTimer(self)
        self.continuous_blink_timer.timeout.connect(self.simulate_blink)

        self.sleep_timer = QTimer(self)
        self.sleep_timer.timeout.connect(self.enter_sleep_mode)

        self.random_wakeup_timer = QTimer(self)
        self.random_wakeup_timer.timeout.connect(self.random_wakeup)

        # Display off timer for the specified timeout duration
        self.display_off_timer = QTimer(self)
        self.display_off_timer.setSingleShot(True)
        self.display_off_timer.timeout.connect(self.turn_off_display_)

        self.schedule_sleep_timer()


    def start_display_off_timer(self):
        if self.display_off:
            return
        """Start the display off timer based on the display_off_timeout_hours from the config."""
        timeout_ms = self.display_off_timeout_hours * 3600 * 1000  # Convert hours to milliseconds
        self.display_off_timer.start(timeout_ms)
        print(f"Display off timer started for {self.display_off_timeout_hours} hours.")

    def turn_off_display_(self):
        if not self.display_off:
            """Turn off the display safely by pausing necessary timers."""
            print("Preparing to turn off display due to timeout.")
            # Pause timers that might conflict with the display being off
            self.inactivity_timer.stop()
            self.continuous_blink_timer.stop()
            self.sleep_timer.stop()
            self.random_wakeup_timer.stop()
            
            self.display_off = True
            turn_off_display()  # Call the function to turn off the display
            print("Display turned off.")

    def turn_on_display_(self):
        """Turn on the display and resume necessary timers."""
        print("Turning on display.")
        turn_on_display()  # Call the function to turn on the display
        self.display_off = False
        
        # Restart or reset timers as needed
        self.reset_inactivity_timer()  # Restart the inactivity timer
        self.exit_sleep_mode()
        print("Timers restarted after turning on display.")
    def reset_inactivity_timer(self):
        """Resets the inactivity timer."""
        self.inactivity_timer.start(500)

    def check_inactivity(self):
        """Checks if enough time has passed since the last image update to start blinking."""
        if time.time() - self.last_image_time > self.inactivity_time_interval:
            self.start_continuous_blinking()

    def start_continuous_blinking(self):
        """Start repeated blinking if no image is received for an extended period."""
        if not self.in_sleep_mode and not self.is_blinking:
            self.inactivity_timer.stop()
            self.simulate_blink()

    def stop_continuous_blinking(self):
        """Stop continuous blinking and reset inactivity timer."""
        self.continuous_blink_timer.stop()
        self.reset_inactivity_timer()

    def schedule_next_blink(self):
        """Schedule the next blink with a randomized interval between min and max intervals."""
        if not self.in_sleep_mode:
            next_blink_interval = random.randint(self.min_blink_interval, self.max_blink_interval)
            self.continuous_blink_timer.start(next_blink_interval)
            print(f"Next blink scheduled in {next_blink_interval} ms")

    def schedule_random_wakeup_timer(self):
            """Schedules the random wakeup timer to trigger after a random interval within the wakeup range."""
            if self.in_sleep_mode:
                wakeup_interval = random.randint(self.min_random_wakeup, self.max_random_wakeup)
                self.random_wakeup_timer.start(wakeup_interval)
                print(f"Random wakeup timer set to {wakeup_interval // (1000 * 60)} minutes")

    def schedule_sleep_timer(self):
        """Schedules the sleep timer with a randomized interval between min and max sleep timeouts."""
        sleep_interval = random.randint(self.min_sleep_timeout, self.max_sleep_timeout)
        self.sleep_timer.start(sleep_interval)
        print(f"Sleep timer scheduled to trigger in {sleep_interval // (1000 * 60)} minutes")

    def enter_sleep_mode(self):
        """Enter sleep mode and display half-closed eye briefly before fully closing."""
        if self.in_sleep_mode or self.display_off:
            return
        if self.is_blinking:
            print("Waiting for blink to finish before entering sleep mode.")
            QTimer.singleShot(300, self.enter_sleep_mode)
            return
        
        self.in_sleep_mode = True
        self.stop_continuous_blinking()
        self.sleep_mode_entered.emit()
        self.display_sleep_images()
        self.schedule_random_wakeup_timer()  # Schedule wakeup timer when entering sleep mode
        self.start_display_off_timer()  # Restart the display off timer each time sleep mode is entered


    def display_sleep_images(self):
        """Display half-closed eye and then closed eye for sleep mode."""
        # Construct filenames for half-closed and closed images
        half_closed_eye_filename = self.app_instance.current_filename[:-5] + "h.jpg"
        closed_eye_filename = self.app_instance.current_filename[:-5] + "c.jpg"

        # Replace third-last character with 'f' for blinking images
        half_closed_eye_filename = half_closed_eye_filename
        closed_eye_filename = closed_eye_filename[:-7] + "csc.jpg"

        # half_closed_eye_filename = self.current_filename[:-6] + "sh.jpg"
        # closed_eye_filename = self.current_filename[:-7] + "csc.jpg"

        # Display half-closed eye briefly
        self.display_image_signal.emit(half_closed_eye_filename)

        # After a brief delay, display the fully closed eye
        QTimer.singleShot(200, lambda: self.display_image_signal.emit(closed_eye_filename))

    def simulate_blink(self):
        """Simulate the blink by toggling images if not in sleep mode or already blinking."""
        if self.in_sleep_mode or self.app_instance.debug_mode_manager.debug_mode or self.is_blinking:
            print("Blinking skipped: in sleep mode, debug mode, or already blinking")
            return

        self.is_blinking = True
        self.blink_started.emit()
        current_filename = self.app_instance.current_filename

        # Construct filenames for half-closed and closed images
        half_closed_eye_filename = self.app_instance.current_filename[:-5] + "h.jpg"
        closed_eye_filename = self.app_instance.current_filename[:-5] + "c.jpg"

        # Replace third-last character with 'f' for blinking images
        half_closed_eye_filename = half_closed_eye_filename
        closed_eye_filename = closed_eye_filename[:-7] + "csc.jpg"

        self.display_image_signal.emit(half_closed_eye_filename)

        QTimer.singleShot(100, lambda: (self.display_image_signal.emit(closed_eye_filename)))
        QTimer.singleShot(300, lambda: (self.display_image_signal.emit(half_closed_eye_filename)))
        QTimer.singleShot(400, lambda: self.end_blinking(current_filename))

    def random_wakeup(self):
        """Simulate a reverse blink by toggling images from closed to open and back to closed, with randomized open duration and eye position."""
        if self.app_instance.debug_mode_manager.debug_mode:
            print("Reverse blink skipped: in sleep mode, debug mode, or already blinking")
            return

        self.is_blinking = True
        self.blink_started.emit()

        # Randomly select an eye position between 0 and 41
        random_position = random.randint(0, 41)
        # Random open duration between 500ms and 1000ms
        open_duration = random.randint(500, 1000)

        # Construct filenames for open, half-closed, and closed images with the random position
        current_filename = self.app_instance.current_filename
        base_filename = f"bt_{random_position:02d}_"
                # Construct filenames for half-closed and closed images
        half_closed_eye_filename = self.app_instance.current_filename[:-5] + "h.jpg"
        open_eye_filename = self.app_instance.current_filename[:-5] + "o.jpg"

        # Start with the closed eye
        self.display_image_signal.emit(current_filename)

        # Transition to half-closed, then open, and finally return to closed with randomized timing
        QTimer.singleShot(100, lambda: self.display_image_signal.emit(half_closed_eye_filename))
        QTimer.singleShot(300, lambda: self.display_image_signal.emit(open_eye_filename))
        QTimer.singleShot(300 + open_duration, lambda: self.display_image_signal.emit(half_closed_eye_filename))
        QTimer.singleShot(400 + open_duration, lambda: self.end_blinking(current_filename))

    def end_blinking(self, original_filename):
        """End the blinking effect and reset the eye to the original state."""
        self.display_image_signal.emit(original_filename)
        print(f"Blinking ended, returned to original image: {original_filename}")
        self.is_blinking = False
        self.blink_ended.emit()
        self.schedule_next_blink()

    def exit_sleep_mode(self):
        """Exit sleep mode and reset timers."""
        if self.in_sleep_mode:
            print("Exiting sleep mode.")
            self.in_sleep_mode = False
            self.reset_inactivity_timer()
            self.schedule_sleep_timer()
            self.sleep_mode_exited.emit()

    def on_blink_interval_changed(self, value):
        """Update the blink interval in live config and restart the inactivity timer."""
        self.min_blink_interval = self.live_config.min_blink_interval
        self.max_blink_interval = self.live_config.max_blink_interval
        self.reset_inactivity_timer()

    def on_sleep_timeout_changed(self):
        """Update the sleep timeout in live config and reschedule the sleep timer."""
        self.min_sleep_timeout = self.live_config.min_sleep_timeout * 1000 * 60
        self.max_sleep_timeout = self.live_config.max_sleep_timeout * 1000 * 60
        self.schedule_sleep_timer()

    def on_random_wakeup_changed(self):
            """Update the random wakeup intervals and reschedule the wakeup timer if in sleep mode."""
            self.min_random_wakeup = self.live_config.min_random_wakeup * 1000 * 60
            self.max_random_wakeup = self.live_config.max_random_wakeup * 1000 * 60
            if self.in_sleep_mode:
                self.schedule_random_wakeup_timer()  # Reschedule wakeup timer if in sleep mode


    def update_last_image_time(self):
        """Update the timestamp of the last image received."""
        self.last_image_time = time.time()
