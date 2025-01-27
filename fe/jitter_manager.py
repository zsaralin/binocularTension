import random
import re
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from display_live_config import DisplayLiveConfig  # Assuming LiveConfig is accessible
import time 
jitter_patterns_0 = [
    [-1, 0],
    [1, 0],
    [-1, 0],
    [1, 0],
    [-1, 0],
    [1, 0],
    [-1, 0],
    [1, 0],
    [-1, 1, 0],
    [1, -1, 0],
    [-1, 1, -1, 0],
    [1, -1, 1, 0],
]
jitter_patterns_1 = [
    [-1, 0],
    [1, 0],
    [-1, 1, 0],
    [1, -1, 0],
    [-1, 1, -1, 0],
    [1, -1, 1, 0],
    [1, 0, -1, 0, 1, 0],
    [-1, -1, 0, 1, 1, 0],
    [1, 1, 0, -1, -1, 0],
    [1, 2, -1, 0],  # Forward with slight backward adjustment
    [-1, -2, 1, 0],  # Backward with slight forward adjustment
    [1, -2, 2, -1, 0],  # Zig-zag with variation
    [-1, 2, -2, 1, 0],  # Reverse zig-zag
    [1, 3, -2, -1, 0],  # Irregular skip-step pattern
    [-1, -3, 2, 1, 0],  # Irregular reverse skip-step pattern
    [0, 1, -2, 3, -1, 0],  # Mixed swing forward
    [0, -1, 2, -3, 1, 0],  # Mixed swing backward
    [1, 2, -3, 4, -2, 1, 0],  # Asymmetric forward movement
    [-1, -2, 3, -4, 2, -1, 0],  # Asymmetric backward movement
    [0, 1, 3, -2, 1, -3, 0],  # Non-linear mixed look-around
    [1, -3, 4, -2, 3, -1, 0],  # Forward-backward irregular look-around
    [-1, 3, -4, 2, -3, 1, 0],  # Reverse irregular look-around
    [1, 4, -3, 2, -1, 0, -2, 3, -4, 1, 0],  # Extended mixed swing
    [-1, -4, 3, -2, 1, 0, 2, -3, 4, -1, 0],  # Extended reverse mixed swing
    [0, 1, 4, -3, 2, -1, 0, -1, -4, 3, -2, 1, 0],  # Complex alternating swing
]

class JitterManager(QObject):
    jitter_started = pyqtSignal()
    jitter_completed = pyqtSignal()

    def __init__(self, main_app, blink_sleep_manager):
        super().__init__()
        self.main_app = main_app
        self.blink_sleep_manager = blink_sleep_manager
        self.live_config = DisplayLiveConfig.get_instance()
        self.last_image_time = time.time()

        self.jitter_start_timer = QTimer(self)
        self.jitter_start_timer.setSingleShot(True)
        self.jitter_start_timer.timeout.connect(self.start_jitter_loop)

        self.jitter_loop_timer = QTimer(self)
        self.jitter_loop_timer.timeout.connect(self.run_jitter)

        self.current_jitter_level = 0
        self.jitter_active = False
        self.active_timers = []

    def start_jitter_process(self):
        """Start the jitter process with a delay."""
        if self.jitter_active:
            return  # Prevent multiple jitter activations
        
        delay = self.live_config.jitter_start_delay * 1000  # Convert to milliseconds
        self.jitter_start_timer.start(int(delay))

    def start_jitter_loop(self):
        """Start the jitter loop after the initial delay."""
        self.run_jitter()

    def run_jitter(self):
        """Run the jitter simulation and schedule the next iteration."""
        self.update_jitter_level()
        if random.random() < self.live_config.nervousness and not self.jitter_active:
            self.simulate_jitter(level=self.current_jitter_level)
        
        jitter_interval = random.randint(
            int(self.live_config.min_jitter_interval * 1000),
            int(self.live_config.max_jitter_interval * 1000)
        )
        self.jitter_loop_timer.start(jitter_interval)

    def update_jitter_level(self):
        """Update the jitter level based on inactivity duration."""
        inactivity_duration = time.time() - self.last_image_time
        self.current_jitter_level = 1 if inactivity_duration > self.live_config.large_jitter_start_delay else 0

    def update_last_image_time(self):
        """Reset jitter timing and level on activity."""
        self.last_image_time = time.time()
        self.jitter_start_timer.stop()
        self.jitter_loop_timer.stop()
        self.current_jitter_level = 0
        self.jitter_active = False
        self.start_jitter_process()

    def stop_all_jitter(self):
        """Stop all active jitter effects."""
        self.jitter_active = False
        for timer in self.active_timers:
            timer.stop()
        self.active_timers.clear()
        print("All jitter effects stopped.")

    def simulate_jitter(self, level=0):
        """Simulate a jitter effect."""
        if self.jitter_active:
            return
        
        self.jitter_active = True  # Lock jitter activity

        patterns = jitter_patterns_0 if level == 0 else jitter_patterns_1
        jitter_pattern = random.choice(patterns)

        if self.main_app.debug_mode_manager.debug_mode or self.blink_sleep_manager.sleep_manager.in_sleep_mode or self.blink_sleep_manager.blink_manager.is_blinking:
            self.jitter_active = False  # Reset if conditions prevent jitter
            return

        current_filename = self.main_app.current_filename
        match = re.match(r"(bt_)(\d+)(_.*\.jpg)", current_filename)
        if not match:
            self.jitter_active = False  # Reset on filename error
            return

        prefix, current_x, rest_of_filename = match.groups()
        current_x = int(current_x)

        jitter_filenames = [
            f"{prefix}{max(0, min(40, current_x + jitter_step))}{rest_of_filename}"
            for jitter_step in jitter_pattern
        ]
        
        delay = 0
        for index, jitter_filename in enumerate(jitter_filenames):
            random_interval = random.randint(self.live_config.min_jitter_speed, self.live_config.max_jitter_speed)
            delay += random_interval
            timer = QTimer()
            timer.singleShot(delay, lambda fn=jitter_filename, idx=index, total=len(jitter_filenames): 
                             self.emit_jittered_filename(fn, idx, total))
            self.active_timers.append(timer)

    def emit_jittered_filename(self, filename, index, total):
        """Emit the jittered filename if not in sleep mode and jitter is active."""
        if not self.jitter_active:
            return

        if not self.blink_sleep_manager.sleep_manager.in_sleep_mode and not self.blink_sleep_manager.blink_manager.is_blinking:
            self.main_app.display_image(filename)
        
        if index == total - 1:
            self.jitter_active = False  # Reset after last image
