import random
from PyQt5.QtCore import QTimer
import os


class RandomWakeupManager:
    def __init__(self, app_instance, sleep_manager):
        self.app_instance = app_instance
        self.in_wakeup = False
        self.sleep_manager = sleep_manager

    def random_wakeup(self):
        """Decide between simple wakeup and look-around wakeup."""
        if self.app_instance.debug_mode_manager.debug_mode or self.in_wakeup or not self.sleep_manager.in_sleep_mode:
            return  # Skip if in wakeup, debug mode, or not in sleep mode
        self.in_wakeup = True  # Set in_wakeup to True since we're starting a wakeup
        look_around = random.random() < 0.9
        if look_around:
            self.random_wakeup_look_around()
        else:
            self.random_wakeup_simple()

    def random_wakeup_simple(self):
        """Perform a simple wakeup sequence."""
        prefix = "bt_"

        random_number = random.randint(0, 40)
        first_letter = random.choice(['c', 'c'])
        second_letter = random.choices(['u', 'd', 's'], weights=[1, 1, 2])[0]
        suffix_open = "o"
        suffix_closed = "c"
        suffix_half_closed = "h"

        initial_filename = f"{prefix}{random_number}_{first_letter}{second_letter}{suffix_open}.jpg"
        half_closed_filename = initial_filename.replace(suffix_open, suffix_half_closed)
        closed_filename = initial_filename.replace(suffix_open, suffix_closed)

        if not os.path.exists(closed_filename):
            closed_filename = closed_filename[:-6] + "sc.jpg"
            if not os.path.exists(closed_filename):
                closed_filename = closed_filename[:-7] + "csc.jpg"

        # Specific durations for each step
        durations = [100, random.randint(500, 1000), 100]

        # Display sequence: h → o → h → c
        self.app_instance.display_image(half_closed_filename)
        QTimer.singleShot(durations[0], lambda: self.app_instance.display_image(initial_filename))
        QTimer.singleShot(durations[0] + durations[1], lambda: self.app_instance.display_image(half_closed_filename))
        QTimer.singleShot(durations[0] + durations[1] + durations[2], lambda: self.app_instance.display_image(closed_filename))

        # Schedule end of wakeup sequence
        total_duration = durations[0] + durations[1] + durations[2]
        QTimer.singleShot(total_duration, self.end_wakeup)

    def random_wakeup_look_around(self):
        """Perform a 'look around' wakeup sequence with jitter patterns."""
        prefix = "bt_"

        random_number = random.randint(0, 40)  # Starting position
        first_letter = random.choice(['c', 'c'])
        second_letter = random.choices(['u', 'd', 's'], weights=[1, 1, 2])[0]
        suffix_open = "o"
        suffix_closed = "c"
        suffix_half_closed = "h"

        initial_filename = f"{prefix}{random_number}_{first_letter}{second_letter}{suffix_open}.jpg"
        half_closed_filename = initial_filename.replace(suffix_open, suffix_half_closed)
        closed_filename = initial_filename.replace(suffix_open, suffix_closed)

        if not os.path.exists(closed_filename):
            closed_filename = closed_filename[:-6] + "sc.jpg"
            if not os.path.exists(closed_filename):
                closed_filename = closed_filename[:-7] + "csc.jpg"

        # Display half-open state first
        self.app_instance.display_image(half_closed_filename)

        # Human-like jitter patterns
        jitter_patterns_1 = [
            [-1, 0], [1, 0],
            [-1, 0, 1], [1, 0, -1],
            [-1, 0, 1, 0, -1], [1, 0, -1, 0, 1],
            [0, 1, 2, 1, 0], [0, -1, -2, -1, 0],
            [0, 1, 2, 3, 2, 1, 0],
            [1, 2, 3, 2, 1, 0, -1],
            [0, 1, 2, 3, 3, 2, 1, 0, -1],
        ]
        chosen_pattern = random.choice(jitter_patterns_1)

        # Generate "look around" positions and durations
        positions = [random_number + offset for offset in chosen_pattern]
        positions = [max(0, min(40, pos)) for pos in positions]  # Clamp within valid range
        filenames = [
            f"{prefix}{pos}_{first_letter}{second_letter}{suffix_open}.jpg" for pos in positions
        ]
        durations = [
            random.randint(200, 400) for _ in filenames[:-2]
        ] + [random.randint(500, 800)] + [100]  # Slightly longer at the end for focus

        # Replace the last filename's suffix with `h` for half-closed state
        if filenames:
            filenames[-1] = filenames[-1].replace(suffix_open, suffix_half_closed)

        # Display "look around" sequence
        total_elapsed_time = 0
        for i, (filename, duration) in enumerate(zip(filenames, durations)):
            # Longer pauses for certain positions to simulate "focus"
            focus_duration = 200 if i in {0, len(filenames) - 2} else 0
            QTimer.singleShot(
                total_elapsed_time,
                lambda fn=filename: self.app_instance.display_image(fn),
            )
            total_elapsed_time += duration + focus_duration

        # Display closed state after the sequence
        QTimer.singleShot(
            total_elapsed_time,
            lambda: self.app_instance.display_image(closed_filename),
        )
        if random.random() < .3:
            QTimer.singleShot(
                total_elapsed_time  +  random.randint(200, 800) ,
                lambda: self.start_another_wakeup() 
            )
        else:
            self.end_wakeup()

    def start_another_wakeup(self):
        """Start another wakeup sequence immediately."""
        print("Starting another random wakeup sequence.")
        # No need to set in_wakeup to True again; it's already True
        self.random_wakeup_look_around()

    def end_wakeup(self):
        """Mark the end of the wakeup sequence."""
        print("Wakeup sequence complete.")
        self.in_wakeup = False  # Reset in_wakeup flag
