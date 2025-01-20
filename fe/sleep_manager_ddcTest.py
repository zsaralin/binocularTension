import random
import time
import os
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
# from turnoff_display import turn_off_display, turn_on_display
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
        sleep_interval = random.randint(self.min_sleep_timeout, self.max_sleep_timeout)
        self.sleep_timer.start(sleep_interval)

    def schedule_random_wakeup_timer(self):
        if self.in_sleep_mode:
            wakeup_interval = random.randint(self.min_random_wakeup, self.max_random_wakeup)
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
        timeout_ms = self.display_off_timeout_hours * 3600 * 1000
        # self.display_off_timer.start(timeout_ms)
        self.display_off_timer.start(int(timeout_ms))
        print(f"Display off timer started for {self.display_off_timeout_hours} hours.")

    def turn_off_display_(self):
        if not self.display_off:
            print("Turning off display...")
            self.sleep_timer.stop()
            self.random_wakeup_timer.stop()
            self.display_off = True
            display_controller = get_display_controller()
            if not display_controller.turn_off_display():
                print("Warning: Failed to turn off display")

    def turn_on_display_(self):
        print("Turning on display...")
        self.display_off_timer.stop()
        self.sleep_timer.stop()
        display_controller = get_display_controller()
        if not display_controller.turn_on_display():
            print("Warning: Failed to turn on display")
        self.display_off = False
        self.exit_sleep_mode()


    def update_last_image_time(self):
        self.last_image_time = time.time()
        self.sleep_timer.stop()
        self.random_wakeup_timer.stop()
        self.display_off_timer.stop()
        self.schedule_sleep_timer()

    def on_sleep_timeout_changed(self):
        self.min_sleep_timeout = self.live_config.min_sleep_timeout * 1000
        self.max_sleep_timeout = self.live_config.max_sleep_timeout * 1000
        self.schedule_sleep_timer()

    def on_random_wakeup_changed(self):
        self.min_random_wakeup = self.live_config.min_random_wakeup * 1000 
        self.max_random_wakeup = self.live_config.max_random_wakeup * 1000 
        if self.in_sleep_mode:
            self.schedule_random_wakeup_timer()
