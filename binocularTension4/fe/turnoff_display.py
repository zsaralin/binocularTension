import os
import threading
import time

nircmd_path = "..\\..\\nircmd-x64\\nircmd.exe"

def turn_off_display():
    """Turns off the display in a separate thread."""
    def _turn_off():
        # Pause any ongoing processes here, if necessary
        # e.g., blink_sleep_manager.pause()
        os.system(f"{nircmd_path} monitor off")
        # Wait a moment to ensure the display is fully off
        time.sleep(0.5)
        # Resume any processes here if needed
        
    threading.Thread(target=_turn_off, daemon=True).start()

def turn_on_display():
    """Turns on the display by simulating a mouse move in a separate thread."""
    def _turn_on():
        # Resume any paused processes here, if necessary
        # e.g., blink_sleep_manager.resume()
        os.system(f"{nircmd_path} sendmouse move 1 1")
        os.system(f"{nircmd_path} sendmouse move -1 -1")
        
    threading.Thread(target=_turn_on, daemon=True).start()

def main():
    while True:
        turn_off_display()
        time.sleep(5)  # Wait for 5 seconds
        turn_on_display()
        time.sleep(5)  # Wait for 5 seconds

if __name__ == "__main__":
    main()
