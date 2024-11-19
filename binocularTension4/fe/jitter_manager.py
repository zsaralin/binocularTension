import random
import re
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from display_live_config import DisplayLiveConfig  # Assuming LiveConfig is accessible

jitter_patterns_0 = [
    [-1, 0],
    [1, 0],
    [-1, 1, 0],
    [1, -1, 0],
    [-1, 1, -1, 0],
    [1, -1, 1, 0],
    [1, 0, -1, 0, 1, 0],
    [-1, -1, 0, 1, 1, 0],
    [1, 1, 0, -1, -1, 0],
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
        self.is_jittering = False
        self.jitter_timer = QTimer(self)
        self.blink_sleep_manager = blink_sleep_manager
        self.live_config = DisplayLiveConfig.get_instance()

    def simulate_jitter(self, level=0):
        patterns = jitter_patterns_0 if level == 0 else jitter_patterns_1
        jitter_pattern = random.choice(patterns)
        """Simulate a jitter by replacing the X coordinate in the filename with jittered values."""
        if self.main_app.debug_mode_manager.debug_mode or self.blink_sleep_manager.sleep_manager.in_sleep_mode:
            print("Jitter effect skipped")
            return
        print('jitter happening ')
        current_filename = self.main_app.current_filename

        # Extract the X coordinate from the filename
        match = re.match(r"(bt_)(\d+)(_.*\.jpg)", current_filename)
        if not match:
            print(f"Filename format error: {current_filename}")
            self.stop_jitters()
            return

        prefix = match.group(1)  # "bt_"
        current_x = int(match.group(2))  # The existing X value
        rest_of_filename = match.group(3)  # The rest of the filename after the X coordinate

        # Scale jitter pattern based on intensity
        jitter_pattern = random.choice(jitter_patterns_1)

        # Generate filenames for each jitter step
        jitter_filenames = [
            f"{prefix}{max(0, min(40, current_x + jitter_step))}{rest_of_filename}"
            for jitter_step in jitter_pattern
        ]

        # Schedule the display of jittered filenames with random intervals
        delay = 0
        for jitter_filename in jitter_filenames:
            random_interval = random.randint(self.live_config.min_jitter_speed, self.live_config.max_jitter_speed)  # Random delay between 100ms and 300ms
            delay += random_interval
            QTimer.singleShot(
                delay, lambda fn=jitter_filename: self.emit_jittered_filename(fn)
            )

    def emit_jittered_filename(self, filename):
        """Emit the jittered filename if not in sleep mode."""
        if not self.blink_sleep_manager.sleep_manager.in_sleep_mode and not self.blink_sleep_manager.blink_manager.is_blinking:
            self.main_app.display_image(filename)
