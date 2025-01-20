from display_control_panel import DisplayControlPanelWidget

class DebugModeManager:
    def __init__(self, parent):
        self.parent = parent
        self.control_panel = None
        self.debug_mode = False

    def toggle_debug_mode(self):
        """Toggle debug mode on or off."""
        self.debug_mode = not self.debug_mode
        print(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}.")

    def toggle_control_panel(self):
        """Toggle the control panel visibility."""
        if self.control_panel is None:
            self.control_panel = DisplayControlPanelWidget(self.parent)
            self.control_panel.show()
        else:
            self.control_panel.close()
            self.control_panel = None

    def parse_filename(self):
        """Parse the filename to extract information like position and mode."""
        parts = self.parent.current_filename.split('_')
        base = parts[0]
        xpos = parts[1].zfill(2)
        depth_ypos_mode = parts[2].split('.')[0]
        depth = depth_ypos_mode[0] if depth_ypos_mode[0] in 'ocw' else 'f'
        ypos = depth_ypos_mode[1] if len(depth_ypos_mode) > 1 else 's'
        mode = depth_ypos_mode[2] if len(depth_ypos_mode) > 2 else 'o'
        return base, xpos, depth, ypos, mode

    def update_display_mode(self, new_mode=None, new_ypos=None, new_xpos=None, new_zpos=None):
        """Update display based on debug mode values."""
        if not self.debug_mode:
            return
        base, xpos, depth, current_ypos, current_mode = self.parse_filename()
        xpos = int(xpos)

        if new_xpos is not None:
            xpos = max(0, min(new_xpos, 201))
        if new_ypos is not None:
            current_ypos = new_ypos
        if new_zpos is not None:
            depth = new_zpos
        if new_mode is not None:
            current_mode = new_mode

        self.update_filename(base, xpos, depth, current_ypos, current_mode)

    def update_filename(self, base, xpos, depth, ypos, mode):
        """Construct the new filename with updated debug parameters."""
        new_filename = f"{base}_{xpos}_{depth}{ypos}{mode}.jpg"
        if new_filename in self.parent.images:
            self.parent.display_image(new_filename)
