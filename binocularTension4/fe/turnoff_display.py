import os

# Path to NirCmd executable
nircmd_path = "C:\\Users\\admin\\Desktop\\nircmd\\nircmd.exe"

def turn_off_display():
    """Turns off the display."""
    os.system(f"{nircmd_path} monitor off")

def turn_on_display():
    """Turns on the display."""
    os.system(f"{nircmd_path} monitor on")


# def turn_off_display():
#     """Simulates turning off the display by setting brightness to 0."""
#     os.system("powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,0)")

# def turn_on_display():
#     """Simulates turning on the display by restoring brightness to 100."""
#     os.system("powershell (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,100)")