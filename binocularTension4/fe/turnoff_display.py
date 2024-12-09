import os
import threading
import time

# Paths to NirCmd and MultiMonitorTool
nircmd_path = "..\\..\\nircmd-x64\\nircmd.exe"
mmt_path = "C:\\Users\\admin\\Desktop\\multimonitortool-x64\MultiMonitorTool.exe"
displays = [
    {
        "id": "\\\\.\\DISPLAY1",
        "resolution": "1920 X 1080",
        "left_top": "0, 0",
        "right_bottom": "1920, 1080",
    },
    {
        "id": "\\\\.\\DISPLAY5",
        "resolution": "1920 X 540",
        "left_top": "1920, 0",
        "right_bottom": "3840, 540",
    },
]

def parse_resolution(resolution):
    """Parses a resolution string like '1920 X 1080' into width and height as integers."""
    width, height = map(int, resolution.split(" X "))
    return width, height

def get_larger_display_id(display_data):
    """Finds the ID of the display with the largest resolution (width × height)."""
    try:
        larger_display = min(
            display_data,
            key=lambda d: parse_resolution(d["resolution"])[0] * parse_resolution(d["resolution"])[1],
        )
        return larger_display["id"]
    except Exception as e:
        print(f"Error determining the larger display: {e}")
        return None

def turn_off_larger_display():
    """Turns off the larger display."""
    larger_display_id = get_larger_display_id(displays)
    if larger_display_id:
        os.system(f'"{mmt_path}" /disable {larger_display_id}')
    else:
        print("No larger display found.")
def turn_on_all_displays():
    for display in displays:
        os.system(f'"{mmt_path}" /enable {display["id"]}')
   
def turn_off_display():
    """Turns off the display in a separate thread."""
    def _turn_off():
        turn_off_larger_display()

    threading.Thread(target=_turn_off, daemon=True).start()

def turn_on_display():
    """Turns on the display by enabling all in a separate thread."""
    def _turn_on():
        turn_on_all_displays()

    threading.Thread(target=_turn_on, daemon=True).start()

def main():
    # while True:
        # print("Turning off the larger display...")
        # turn_off_display()
        # time.sleep(5)  # Wait for 5 seconds
        # print("Turning on all displays...")
        turn_on_display()
        time.sleep(10)  # Wait for 10 seconds

if __name__ == "__main__":
    main()
