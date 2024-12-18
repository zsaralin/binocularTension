import subprocess
import time

def turn_off_display():
    """
    Turn off the HDMI display by switching to the internal display only.
    """
    try:
        print("Turning off HDMI display...")
        subprocess.run(["DisplaySwitch.exe", "/external"], check=True) # should be external 
        print("HDMI display successfully turned off.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing DisplaySwitch to turn off HDMI: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def turn_on_display():
    """
    Turn on the HDMI display by extending the display to the external HDMI.
    """
    try:
        print("Turning on HDMI display...")
        subprocess.run(["DisplaySwitch.exe", "/extend"], check=True)
        print("HDMI display successfully turned on.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing DisplaySwitch to turn on HDMI: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Example usage
if __name__ == "__main__":
    turn_off_display()
    time.sleep(5)  # Wait for 5 seconds before turning it back on
    turn_on_display()
