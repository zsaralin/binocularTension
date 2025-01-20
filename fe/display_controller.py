import subprocess
import logging
import time
from typing import Optional, Dict, List

class DisplayController:
    """
    Handles display power control using DDC/CI via WinDDCutil with fallback to DisplaySwitch.exe
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._displays = {}
        self._last_states = {}
        self._use_ddc = True  # Will be set to False if DDC fails
        
    def _run_ddc_command(self, command: List[str]) -> Optional[str]:
        """Execute a winddcutil command."""
        try:
            result = subprocess.run(
                ["winddcutil"] + command,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error(f"DDC command failed: {e}")
            self._use_ddc = False  # Disable DDC after failure
            return None

    def _run_display_switch(self, command: str) -> bool:
        """Fallback to DisplaySwitch.exe."""
        try:
            subprocess.run(["DisplaySwitch.exe", command], check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"DisplaySwitch failed: {e}")
            return False

    def get_displays(self, force_refresh=False) -> Dict[str, Dict]:
        """Get information about connected displays."""
        if not force_refresh and self._displays:
            return self._displays
            
        if not self._use_ddc:
            return {}
            
        displays = {}
        output = self._run_ddc_command(["detect"])
        
        if output:
            for line in output.split('\n'):
                line = line.strip()
                if line and line[0].isdigit():  # Lines starting with a number
                    parts = line.split(' ', 1)  # Split on first space
                    if len(parts) == 2:
                        display_id = parts[0]
                        display_name = parts[1]
                        displays[display_id] = {
                            'name': display_name,
                            'id': display_id
                        }
                        
        self._displays = displays
        return displays

    def turn_off_display(self) -> bool:
        """
        Turn off display(s) using DDC if available, fallback to DisplaySwitch.
        Returns True if successful, False otherwise.
        """
        success = False
        
        if self._use_ddc:
            # self.logger.info("Attempting to turn off displays using DDC...")
            print("Attempting to turn off displays using DDC...")
            displays = self.get_displays().keys()
            print("Displays: ", displays)
            
            for index, display_id in enumerate(displays):
                print("Display ID: ", display_id)
                print("Index: ", index)
                if index == 0:
                    # self.logger.info(f"Skipping turning off the first display {display_id}")
                    print(f"Skipping turning off the first display {display_id}")
                    continue
                
                # Cache current state
                self._last_states[display_id] = "on"
                
                # Send DDC command
                result = self._run_ddc_command([
                    "setvcp",
                    str(display_id),
                    "D6", "05"  # Power control: off
                ])
                
                if result is not None:
                    success = True
                    self.logger.info(f"Successfully turned off display {display_id} using DDC")
                else:
                    self.logger.warning(f"Failed to turn off display {display_id} using DDC")
        
        if not success:
            self.logger.info("Falling back to DisplaySwitch...")
            success = self._run_display_switch("/external")
            
        return success

    def turn_on_display(self) -> bool:
        """
        Turn on display(s) using DDC if available, fallback to DisplaySwitch.
        Returns True if successful, False otherwise.
        """
        success = False

        print("Entering Turn On Display")
        
        if self._use_ddc:
            result = self._run_ddc_command([
                        "setvcp",
                        str(2),
                        "D6", "1"  # Power control: on
                    ])
        if False:
            self.logger.info("Attempting to turn on displays using DDC...")
            print("Attempting to turn on displays using DDC...")
            displays = self.get_displays().keys()
            print(displays)
            for display_id in displays:
                # Only try to turn on displays we know were on before
                # if self._last_states.get(display_id) == "on":
                if True:
                    result = self._run_ddc_command([
                        "setvcp",
                        str(display_id),
                        "D6", "1"  # Power control: on
                    ])
                    
                    if result is not None:
                        success = True
                        self.logger.info(f"Successfully turned on display {display_id} using DDC")
                    else:
                        self.logger.warning(f"Failed to turn on display {display_id} using DDC")
        
        if not success:
            self.logger.info("Falling back to DisplaySwitch...")
            print("Falling back to DisplaySwitch...")
            success = self._run_display_switch("/extend")
            
        return success

    def get_display_state(self, display_id: str) -> Optional[str]:
        """Get current power state of a display."""
        if not self._use_ddc:
            return None
            
        result = self._run_ddc_command([
            "getvcp",
            "--display", display_id,
            "D6"
        ])
        
        if result:
            try:
                value = int(result.split('=')[1].strip())
                return "on" if value == 1 else "off"
            except (IndexError, ValueError):
                self.logger.error(f"Failed to parse power state for display {display_id}")
        
        return None

# Create singleton instance
_display_controller = None

def get_display_controller() -> DisplayController:
    """Get or create the singleton DisplayController instance."""
    global _display_controller
    if _display_controller is None:
        _display_controller = DisplayController()
    return _display_controller




# winddcutil setvcp 2 D6 05


# Displays:  dict_keys(['1', '2'])
# Display ID:  1
# Index:  0
# Skipping turning off the first display 1
# Display ID:  2
# Index:  1
# DDC command failed: Command '['winddcutil', 'setvcp', '--display', '2', 'D6', '05']' returned non-zero exit status 2.
# Failed to turn off display 2 using DDC