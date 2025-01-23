import json
import os
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QLineEdit,
    QPushButton, QCheckBox, QSpinBox, QComboBox
)

from display_live_config import DisplayLiveConfig


class DisplayControlPanelWidget(QWidget):
    """
    Control panel for tweaking display settings (blink, sleep, etc.)
    and choosing between Female/Male or auto‐switch, via VersionSelector.
    """

    # Optional signals for other parts of your application
    min_blink_interval_changed = pyqtSignal(int)
    max_blink_interval_changed = pyqtSignal(int)
    min_sleep_timeout_changed = pyqtSignal(int)
    max_sleep_timeout_changed = pyqtSignal(int)
    min_random_wakeup_changed = pyqtSignal(int)
    max_random_wakeup_changed = pyqtSignal(int)
    display_off_timeout_changed = pyqtSignal(int)

    def __init__(self, display, main_display, version_selector, parent=None):
        """
        :param display: Some object that handles "update_display_mode(...)" etc.
        :param main_display: The main display widget that actually shows Female/Male frames.
        """
        super().__init__(parent)

        self.sliders = {}

        self.display = display
        self.main_display = main_display
        self.version_selector = version_selector

        # 1. Load configuration from JSON (or defaults)
        self.config = self.load_config()

        # 2. Access the shared "live" config object
        self.live_config = DisplayLiveConfig.get_instance()


        # 4. Initialize internal values from config (store in single‐element lists for easy slider usage)
        self.min_blink_interval = [self.config.get("min_blink_interval", 3)]
        self.max_blink_interval = [self.config.get("max_blink_interval", 8)]
        self.min_sleep_timeout = [self.config.get("min_sleep_timeout", 60)]
        self.max_sleep_timeout = [self.config.get("max_sleep_timeout", 180)]
        self.min_random_wakeup = [self.config.get("min_random_wakeup", 30)]
        self.max_random_wakeup = [self.config.get("max_random_wakeup", 60)]
        self.blink_speed = [self.config.get("blink_speed", 5)]
        self.jitter_start_delay = [self.config.get("jitter_start_delay", 0.5)]
        self.large_jitter_start_delay = [self.config.get("large_jitter_start_delay", 60)]
        self.min_jitter_interval = [self.config.get("min_jitter_interval", 3)]
        self.max_jitter_interval = [self.config.get("max_jitter_interval", 6)]
        self.min_jitter_speed = [self.config.get("min_jitter_speed", 500)]
        self.max_jitter_speed = [self.config.get("max_jitter_speed", 800)]
        self.display_off_timeout = [self.config.get("display_off_timeout", 1)]
        self.stretch_x = [self.config.get("stretch_x", 1.0)]
        self.stretch_y = [self.config.get("stretch_y", 1.0)]
        self.smooth_y = [self.config.get("smooth_y", 10)]
        self.rotate = [self.config.get("rotate", 0)]
        self.nervousness = [self.config.get("nervousness", 0.8)]

        # For debug mode + checkboxes
        self.checkbox_states = {
            "debug": False,
            "open": False,
            "closed": False,
            "half": False,
            "surprised": False
        }

        # 5. Build the entire UI
        self.init_ui()

        # 6. Let the VersionSelector read its portion of the config (auto_switch_enabled, etc.)
        self.version_selector.load_state_from_dict(self.config)

        # 7. Sync these local values into the LiveConfig object
        self.sync_with_live_config()

    # --------------------------------------------------------------------------
    #                        CONFIG LOAD/SAVE
    # --------------------------------------------------------------------------

    def load_config(self):
        """
        Load from 'display_config.json' if it exists and is valid,
        otherwise return sensible defaults.
        """
        try:
            with open('display_config.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return defaults
            return {
                "min_blink_interval": 3,
                "max_blink_interval": 8,
                "min_sleep_timeout": 60,
                "max_sleep_timeout": 180,
                "min_random_wakeup": 30,
                "max_random_wakeup": 60,
                "blink_speed": 5,
                "jitter_start_delay": 0.5,
                "large_jitter_start_delay": 60,
                "min_jitter_interval": 3,
                "max_jitter_interval": 6,
                "min_jitter_speed": 500,
                "max_jitter_speed": 800,
                "display_off_timeout": 1,
                "stretch_x": 1.0,
                "stretch_y": 1.0,
                "smooth_y": 10,
                "rotate": 0,
                "nervousness": 0.8,
                "selected_folder": "female",
                "auto_switch_enabled": False,
                "auto_switch_interval_low": 0.5,
                "auto_switch_interval_high": 0.5
            }



    def save_config(self):
        version_info = self.version_selector.save_state_to_dict()
        config_data = {}
        config_data["min_blink_interval"] = self.sliders["min_blink_interval"].current_value()
        config_data["max_blink_interval"] = self.sliders["max_blink_interval"].current_value()
        config_data["min_sleep_timeout"] = self.sliders["min_sleep_timeout"].current_value()
        config_data["max_sleep_timeout"] = self.sliders["max_sleep_timeout"].current_value()
        config_data["min_random_wakeup"] = self.sliders["min_random_wakeup"].current_value()
        config_data["max_random_wakeup"] = self.sliders["max_random_wakeup"].current_value()
        config_data["blink_speed"] = self.sliders["blink_speed"].current_value()
        config_data["jitter_start_delay"] = self.sliders["jitter_start_delay"].current_value()
        config_data["large_jitter_start_delay"] = self.sliders["large_jitter_start_delay"].current_value()
        config_data["min_jitter_interval"] = self.sliders["min_jitter_interval"].current_value()
        config_data["max_jitter_interval"] = self.sliders["max_jitter_interval"].current_value()
        config_data["min_jitter_speed"] = self.sliders["min_jitter_speed"].current_value()
        config_data["max_jitter_speed"] = self.sliders["max_jitter_speed"].current_value()
        config_data["display_off_timeout"] = self.sliders["display_off_timeout"].current_value()
        config_data["stretch_x"] = self.sliders["stretch_x"].current_value()
        config_data["stretch_y"] = self.sliders["stretch_y"].current_value()
        config_data["smooth_y"] = self.sliders["smooth_y"].current_value()
        config_data["rotate"] = self.sliders["rotate"].current_value()
        config_data["nervousness"] = self.sliders["nervousness"].current_value()
        config_data.update(version_info)
        """Save current settings to config file."""
        # config_data = {
        #     "min_blink_interval": self.min_blink_interval[0],
        #     "max_blink_interval": self.max_blink_interval[0],
        #     "min_sleep_timeout": self.min_sleep_timeout[0],
        #     "max_sleep_timeout": self.max_sleep_timeout[0],
        #     "min_random_wakeup": self.min_random_wakeup[0],
        #     "max_random_wakeup": self.max_random_wakeup[0],
        #     "blink_speed": self.blink_speed[0],
        #     "jitter_start_delay": self.jitter_start_delay[0], 
        #     "large_jitter_start_delay": self.large_jitter_start_delay[0],
        #     "min_jitter_interval": self.min_jitter_interval[0],
        #     "max_jitter_interval": self.max_jitter_interval[0],
        #     "min_jitter_speed": self.min_jitter_speed[0],
        #     "max_jitter_speed": self.max_jitter_speed[0],
        #     "display_off_timeout": self.display_off_timeout[0],
        #     "stretch_x": self.stretch_x[0],
        #     "stretch_y": self.stretch_y[0],
        #     "smooth_y": self.smooth_y[0],
        #     "rotate": self.rotate[0],
        #     "nervousness": self.nervousness[0],
        #     **version_info  # Merge selected_folder, auto_switch_enabled, auto_switch_interval_low, auto_switch_interval_high
        # }

        try:
            with open('display_config.json', 'w') as f:
                json.dump(config_data, f, indent=4)
            print("Configuration saved successfully")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    # --------------------------------------------------------------------------
    #                        CLOSE / KEY EVENTS
    # --------------------------------------------------------------------------

    def closeEvent(self, event):
        """
        On panel close, simply save config. If auto‐switch was active, it keeps going.
        """
        self.save_config()
        self.main_display.control_panel = None
        # Optionally hide the mouse cursor in your main display
        self.main_display.setCursor(Qt.BlankCursor)
        self.main_display.activateWindow()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """
        Forward certain bracket keys to main_display, or handle locally if needed.
        """
        if event.key() in [Qt.Key_BracketLeft, Qt.Key_BracketRight, Qt.Key_G]:
            self.main_display.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    # --------------------------------------------------------------------------
    #                        MAIN UI CONSTRUCTION
    # --------------------------------------------------------------------------

    def init_ui(self):
        """
        Build the entire control panel UI:
          1. Add version selector (Auto/Male/Female) from VersionSelector
          2. Add blink/sleep/jitter sliders
          3. Add debug mode and advanced checkboxes
          4. Add a save button
        """
        main_layout = QVBoxLayout(self)

        #
        # 1) VersionSelector UI
        #
        # self.version_selector.setup_ui(main_layout)
        main_layout.addSpacing(10)

        #
        # 2) Sliders for blink, sleep, jitters, etc.
        #
        # self.create_slider_group(main_layout, "Min Blink Interval (s)",
        #                          self.min_blink_interval, 1, 20, 1)
        self.create_slider_group(
            layout=main_layout,
            setting_name="min_blink_interval",
            label_text="Min Blink Interval (s)",
            initial_value=self.min_blink_interval[0],
            min_val=1,
            max_val=20,
            step=1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="max_blink_interval",
            label_text="Max Blink Interval (s)",
            initial_value=self.max_blink_interval[0],
            min_val=1,
            max_val=20,
            step=1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="min_sleep_timeout",
            label_text="Min Sleep Timeout (s)",
            initial_value=self.min_sleep_timeout[0],
            min_val=1,
            max_val=300,
            step=1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="max_sleep_timeout",
            label_text="Max Sleep Timeout (s)",
            initial_value=self.max_sleep_timeout[0],
            min_val=1,
            max_val=300,
            step=1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="min_random_wakeup",
            label_text="Min Random Wakeup (s)",
            initial_value=self.min_random_wakeup[0],
            min_val=1,
            max_val=300,
            step=1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="max_random_wakeup",
            label_text="Max Random Wakeup (s)",
            initial_value=self.max_random_wakeup[0],
            min_val=1,
            max_val=300,
            step=1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="jitter_start_delay",
            label_text="Jitter Start Delay (s)",
            initial_value=self.jitter_start_delay[0],
            min_val=0,
            max_val=1000,
            step=0.1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="large_jitter_start_delay",
            label_text="Large Jitter Start Delay (s)",
            initial_value=self.large_jitter_start_delay[0],
            min_val=1,
            max_val=1000,
            step=1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="min_jitter_speed",
            label_text="Min Jitter Speed (ms)",
            initial_value=self.min_jitter_speed[0],
            min_val=100,
            max_val=1000,
            step=1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="max_jitter_speed",
            label_text="Max Jitter Speed (ms)",
            initial_value=self.max_jitter_speed[0],
            min_val=100,
            max_val=2000,
            step=1
        )

        self.create_slider_group(
            layout=main_layout,
            setting_name="display_off_timeout",
            label_text="Display Off Timeout (s)",
            initial_value=self.display_off_timeout[0],
            min_val=0.1,
            max_val=300,
            step=0.1
        )

        
        self.create_slider_group(
            layout=main_layout,
            setting_name="min_jitter_interval",
            label_text="Min Jitter Interval (s)",
            initial_value=self.min_jitter_interval[0],
            min_val=1,
            max_val=300,
            step=1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="max_jitter_interval",
            label_text="Max Jitter Interval (s)",
            initial_value=self.max_jitter_interval[0],
            min_val=1,
            max_val=300,
            step=1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="blink_speed",
            label_text="Blink Speed",
            initial_value=self.blink_speed[0],
            min_val=1,
            max_val=20,
            step=1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="stretch_x",
            label_text="Stretch X",
            initial_value=self.stretch_x[0],
            min_val=1,
            max_val=1.5,
            step=0.01
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="stretch_y",
            label_text="Stretch Y",
            initial_value=self.stretch_y[0],
            min_val=1,
            max_val=1.5,
            step=0.01
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="smooth_y",
            label_text="Smooth Y",
            initial_value=self.smooth_y[0],
            min_val=0,
            max_val=100,
            step=1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="rotate",
            label_text="Rotate",
            initial_value=self.rotate[0],
            min_val=-5,
            max_val=5,
            step=0.1
        )
        
        self.create_slider_group(
            layout=main_layout,
            setting_name="nervousness",
            label_text="Nervousness",
            initial_value=self.nervousness[0],
            min_val=0,
            max_val=1,
            step=0.1
        )

        #
        # 3) Debug mode + advanced checkboxes
        #
        checkbox_layout = QVBoxLayout()
        self.debug_checkbox = QCheckBox("Debug")
        self.debug_checkbox.stateChanged.connect(self.on_debug_checkbox_changed)
        checkbox_layout.addWidget(self.debug_checkbox)

        # Additional mode checkboxes
        self.open_checkbox = QCheckBox("Open")
        self.open_checkbox.stateChanged.connect(lambda state:
            self.display.update_display_mode(new_mode='o' if state else None))
        checkbox_layout.addWidget(self.open_checkbox)

        self.closed_checkbox = QCheckBox("Closed")
        self.closed_checkbox.stateChanged.connect(lambda state:
            self.display.update_display_mode(new_mode='c' if state else None))
        checkbox_layout.addWidget(self.closed_checkbox)

        self.half_checkbox = QCheckBox("Half")
        self.half_checkbox.stateChanged.connect(lambda state:
            self.display.update_display_mode(new_mode='h' if state else None))
        checkbox_layout.addWidget(self.half_checkbox)

        self.surprised_checkbox = QCheckBox("Surprised")
        self.surprised_checkbox.stateChanged.connect(lambda state:
            self.display.update_display_mode(new_mode='w' if state else None))
        checkbox_layout.addWidget(self.surprised_checkbox)

        # Start hidden until debug mode is enabled
        self.open_checkbox.setVisible(False)
        self.closed_checkbox.setVisible(False)
        self.half_checkbox.setVisible(False)
        self.surprised_checkbox.setVisible(False)

        # X Position SpinBox
        self.xpos_widget = QWidget()
        xpos_layout = QHBoxLayout(self.xpos_widget)
        self.xpos_label = QLabel("X Position:")
        xpos_layout.addWidget(self.xpos_label)
        self.xpos_spinbox = QSpinBox()
        self.xpos_spinbox.setRange(0, 41)
        self.xpos_spinbox.setValue(0)
        self.xpos_spinbox.valueChanged.connect(lambda v:
            self.display.update_display_mode(new_xpos=v))
        xpos_layout.addWidget(self.xpos_spinbox)
        self.xpos_widget.setVisible(False)
        checkbox_layout.addWidget(self.xpos_widget)

        # Y Position Dropdown
        self.ypos_widget = QWidget()
        ypos_layout = QHBoxLayout(self.ypos_widget)
        self.ypos_label = QLabel("Y Position")
        ypos_layout.addWidget(self.ypos_label)
        self.ypos_dropdown = QComboBox()
        self.ypos_dropdown.addItems(["Up", "Straight", "Down"])
        self.ypos_dropdown.setCurrentText("Straight")
        self.ypos_dropdown.currentTextChanged.connect(lambda text:
            self.display.update_display_mode(new_ypos={'Up': 'u','Straight': 's','Down': 'd'}[text]))
        ypos_layout.addWidget(self.ypos_dropdown)
        self.ypos_widget.setVisible(False)
        checkbox_layout.addWidget(self.ypos_widget)

        # Z Position Dropdown
        self.zpos_widget = QWidget()
        zpos_layout = QHBoxLayout(self.zpos_widget)
        self.zpos_label = QLabel("Z Position")
        zpos_layout.addWidget(self.zpos_label)
        self.zpos_dropdown = QComboBox()
        self.zpos_dropdown.addItems(["Close", "Far"])
        self.zpos_dropdown.setCurrentText("Close")
        self.zpos_dropdown.currentTextChanged.connect(lambda text:
            self.display.update_display_mode(new_zpos={'Close': 'c', 'Far': 'f'}[text]))
        zpos_layout.addWidget(self.zpos_dropdown)
        self.zpos_widget.setVisible(False)
        checkbox_layout.addWidget(self.zpos_widget)

        main_layout.addLayout(checkbox_layout)

        #
        # 4) Save button
        #
        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        main_layout.addWidget(save_button)

        reset_button = QPushButton("Return to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        main_layout.addWidget(reset_button)

        self.setLayout(main_layout)


    def reset_to_defaults(self):
        try:
            # Load the defaults from the default JSON file
            with open('default_display_config.json', 'r') as f:
                defaults = json.load(f)

            # Map of config names to their corresponding single-element lists
            settings_map = {
                'min_blink_interval': self.min_blink_interval,
                'max_blink_interval': self.max_blink_interval,
                'min_sleep_timeout': self.min_sleep_timeout,
                'max_sleep_timeout': self.max_sleep_timeout,
                'min_random_wakeup': self.min_random_wakeup,
                'max_random_wakeup': self.max_random_wakeup,
                'blink_speed': self.blink_speed,
                'jitter_start_delay': self.jitter_start_delay,
                'large_jitter_start_delay': self.large_jitter_start_delay,
                'min_jitter_interval': self.min_jitter_interval,
                'max_jitter_interval': self.max_jitter_interval,
                'min_jitter_speed': self.min_jitter_speed,
                'max_jitter_speed': self.max_jitter_speed,
                'display_off_timeout': self.display_off_timeout,
                'stretch_x': self.stretch_x,
                'stretch_y': self.stretch_y,
                'smooth_y': self.smooth_y,
                'rotate': self.rotate,
                'nervousness': self.nervousness
            }

            for setting_name, target_list in settings_map.items():
                new_val = defaults.get(setting_name, target_list[0])

                slider_group = self.sliders.get(setting_name)
                if slider_group is not None:
                    slider_group.set_value(new_val)



            # for setting_name, target_list in settings_map.items():
            #     new_val = defaults.get(setting_name, target_list[0])
            #     target_list[0] = new_val

            #     # Update the QSlider
            #     slider = self.findChild(QSlider, setting_name)

            #     print(f"Setting {setting_name} to {new_val} with slider {slider}")

            #     if slider is not None:
            #         step = slider.singleStep()
            #         slider.setValue(int(new_val / step))

            #     # Update the QLineEdit
            #     lineedit = self.findChild(QLineEdit, setting_name)
            #     if lineedit is not None:
            #         lineedit.setText(f"{new_val:.1f}")


            self.sync_with_live_config()
            self.save_config()
            print("Defaults applied and GUI updated.")
        except Exception as e:
            print(f"Error resetting to defaults: {e}")


    # --------------------------------------------------------------------------
    #                        SLIDER CREATION / CALLBACKS
    # --------------------------------------------------------------------------

    # def create_slider_group(self, layout, label_text, target_list,
    #                         min_val, max_val, step):
    #     """
    #     Create a horizontal slider + label + QLineEdit group.
    #       - target_list is a single‐element list, e.g. self.min_blink_interval
    #       - step controls how we scale the slider to int range
    #       - we update the live config whenever the slider moves
    #     """
    #     hbox = QHBoxLayout()

    #     scaled_min = int(min_val / step)
    #     scaled_max = int(max_val / step)
    #     scaled_value = int(target_list[0] / step)

    #     label = QLabel(label_text)
    #     setting_key = label_text.lower().replace(' ', '_').replace('(', '').replace(')', '')
    #     # if setting key ends in _s or _ms, remove the _s or _ms
    #     if setting_key.endswith('_s'):
    #         setting_key = setting_key[:-2]
    #     elif setting_key.endswith('_ms'):
    #         setting_key = setting_key[:-3]


    #     print(f"Setting key: {setting_key}")
    #     slider = QSlider(Qt.Horizontal, self)
    #     slider.setObjectName(setting_key)
    #     slider.setRange(scaled_min, scaled_max)
    #     slider.setValue(scaled_value)

    #     value_label = QLabel(f"{target_list[0]:.1f}")
    #     value_label.setAlignment(Qt.AlignRight)
    #     input_field = QLineEdit(f"{target_list[0]:.1f}", self)
    #     input_field.setObjectName(setting_key)
    #     input_field.setFixedWidth(50)
    #     input_field.setAlignment(Qt.AlignCenter)

    #     # Handle text input → slider
    #     def on_input_returned():
    #         print(f"Input returned: {input_field.text()}")
    #         try:
    #             val = float(input_field.text())
    #             val = max(min(val, max_val), min_val)
    #             slider.setValue(int(val / step))
    #         except ValueError:
    #             pass

    #     input_field.textChanged.connect(on_input_returned)

    #     # Handle slider → label, text, and the underlying variable
    #     def on_slider_value_changed(value):
    #         print(f"Slider value changed: {value}")
    #         real_val = value * step
    #         value_label.setText(f"{real_val:.1f}")
    #         input_field.setText(f"{real_val:.1f}")
    #         self.update_value(target_list, real_val)

    #     slider.valueChanged.connect(on_slider_value_changed)

    #     hbox.addWidget(label)
    #     hbox.addWidget(slider)
    #     hbox.addWidget(value_label)
    #     hbox.addWidget(input_field)
    #     layout.addLayout(hbox)

    def create_slider_group(self, layout, setting_name, label_text,
                            initial_value, min_val, max_val, step):
        """
        Creates a SliderGroup widget and stores it in self.sliders.
        """
        group = SliderGroup(label_text, initial_value, min_val, max_val, step, parent=self)
        layout.addWidget(group)
        self.sliders[setting_name] = group


    def update_value(self, target_list, value):
        """
        Store new numeric value in the single‐element list and also
        update the live_config or emit signals as needed.
        """
        target_list[0] = value
        print(f"Updated value: {value} for {target_list}")

        # Update the shared DisplayLiveConfig
        if target_list is self.min_blink_interval:
            self.live_config.min_blink_interval = value
            self.min_blink_interval_changed.emit(int(value))
        elif target_list is self.max_blink_interval:
            self.live_config.max_blink_interval = value
            self.max_blink_interval_changed.emit(int(value))
        elif target_list is self.min_sleep_timeout:
            self.live_config.min_sleep_timeout = value
            self.min_sleep_timeout_changed.emit(int(value))
        elif target_list is self.max_sleep_timeout:
            self.live_config.max_sleep_timeout = value
            self.max_sleep_timeout_changed.emit(int(value))
        elif target_list is self.min_random_wakeup:
            self.live_config.min_random_wakeup = value
            self.min_random_wakeup_changed.emit(int(value))
        elif target_list is self.max_random_wakeup:
            self.live_config.max_random_wakeup = value
            self.max_random_wakeup_changed.emit(int(value))
        elif target_list is self.blink_speed:
            self.live_config.blink_speed = value
        elif target_list is self.jitter_start_delay:
            self.live_config.jitter_start_delay = value
        elif target_list is self.large_jitter_start_delay:
            self.live_config.large_jitter_start_delay = value
        elif target_list is self.min_jitter_interval:
            self.live_config.min_jitter_interval = value
        elif target_list is self.max_jitter_interval:
            self.live_config.max_jitter_interval = value
        elif target_list is self.min_jitter_speed:
            self.live_config.min_jitter_speed = value
        elif target_list is self.max_jitter_speed:
            self.live_config.max_jitter_speed = value
        elif target_list is self.display_off_timeout:
            self.live_config.display_off_timeout = value
            self.display_off_timeout_changed.emit(int(value))
        elif target_list is self.stretch_x:
            self.live_config.stretch_x = value
        elif target_list is self.stretch_y:
            self.live_config.stretch_y = value
        elif target_list is self.smooth_y:
            self.live_config.smooth_y = value
        elif target_list is self.rotate:
            self.live_config.rotate = value
        elif target_list is self.nervousness:
            self.live_config.nervousness = value

    # --------------------------------------------------------------------------
    #                        SYNCHRONIZE LIVE CONFIG
    # --------------------------------------------------------------------------

    def sync_with_live_config(self):
        """
        Initialize the DisplayLiveConfig object with our local settings
        so everything is consistent on startup.
        """
        self.live_config.min_blink_interval = self.min_blink_interval[0]
        self.live_config.max_blink_interval = self.max_blink_interval[0]
        self.live_config.min_sleep_timeout = self.min_sleep_timeout[0]
        self.live_config.max_sleep_timeout = self.max_sleep_timeout[0]
        self.live_config.min_random_wakeup = self.min_random_wakeup[0]
        self.live_config.max_random_wakeup = self.max_random_wakeup[0]
        self.live_config.blink_speed = self.blink_speed[0]
        self.live_config.jitter_start_delay = self.jitter_start_delay[0]
        self.live_config.large_jitter_start_delay = self.large_jitter_start_delay[0]
        self.live_config.min_jitter_interval = self.min_jitter_interval[0]
        self.live_config.max_jitter_interval = self.max_jitter_interval[0]
        self.live_config.min_jitter_speed = self.min_jitter_speed[0]
        self.live_config.max_jitter_speed = self.max_jitter_speed[0]
        self.live_config.display_off_timeout = self.display_off_timeout[0]
        self.live_config.stretch_x = self.stretch_x[0]
        self.live_config.stretch_y = self.stretch_y[0]
        self.live_config.smooth_y = self.smooth_y[0]
        self.live_config.rotate = self.rotate[0]
        self.live_config.nervousness = self.nervousness[0]

    # --------------------------------------------------------------------------
    #                        DEBUG MODE / ADVANCED CHECKBOXES
    # --------------------------------------------------------------------------

    def on_debug_checkbox_changed(self, state):
        """
        Show/hide advanced checkboxes and update display if needed.
        """
        checked = (state == Qt.Checked)
        self.display.debug_mode = checked
        print(f"Debug mode {'enabled' if checked else 'disabled'}.")

        # Show advanced checkboxes if in debug mode
        self.open_checkbox.setVisible(checked)
        self.closed_checkbox.setVisible(checked)
        self.half_checkbox.setVisible(checked)
        self.surprised_checkbox.setVisible(checked)

        # Show X/Y/Z position if in debug mode
        self.xpos_widget.setVisible(checked)
        self.ypos_widget.setVisible(checked)
        self.zpos_widget.setVisible(checked)

        if checked:
            # Example: parse filename to guess mode
            base, xpos, depth, current_ypos, current_mode = self.display.parse_filename()
            # Update UI controls
            self.xpos_spinbox.setValue(int(xpos))

            if current_ypos.lower() == 'u':
                self.ypos_dropdown.setCurrentText("Up")
            elif current_ypos.lower() == 's':
                self.ypos_dropdown.setCurrentText("Straight")
            elif current_ypos.lower() == 'd':
                self.ypos_dropdown.setCurrentText("Down")

            if depth.lower() == 'c':
                self.zpos_dropdown.setCurrentText("Close")
            elif depth.lower() == 'f':
                self.zpos_dropdown.setCurrentText("Far")



class SliderGroup(QWidget):
    """
    A self-contained widget that has:
      - A label (descriptive)
      - A horizontal slider
      - A line edit for numeric input
      - An optional real-time value label
    It also handles synchronizing the slider and the line edit.
    """

    def __init__(self, label_text: str, initial_value: float,
                 min_val: float, max_val: float, step: float, parent=None):
        super().__init__(parent)

        self.label_text = label_text
        self.min_val = min_val
        self.max_val = max_val
        self.step = step

        layout = QHBoxLayout(self)

        # Label
        self.label_widget = QLabel(label_text, self)
        layout.addWidget(self.label_widget)

        # Slider
        self.slider = QSlider(Qt.Horizontal, self)
        # We scale the slider’s range by (1 / step)
        self.slider.setRange(int(min_val / step), int(max_val / step))
        self.slider.setValue(int(initial_value / step))
        layout.addWidget(self.slider)

        # (Optional) a small label to display the numeric value in real time
        self.value_label = QLabel(f"{initial_value:.1f}", self)
        self.value_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.value_label)

        # LineEdit
        self.line_edit = QLineEdit(f"{initial_value:.1f}", self)
        self.line_edit.setFixedWidth(50)
        self.line_edit.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.line_edit)

        # Wire signals
        self.slider.valueChanged.connect(self.on_slider_changed)
        self.line_edit.textChanged.connect(self.on_text_changed)

    def on_slider_changed(self, slider_pos: float):
        """When the slider moves, update the line edit and the label."""
        new_val = slider_pos * self.step
        self.value_label.setText(f"{new_val:.1f}")
        self.line_edit.setText(f"{new_val:.1f}")

    #     def on_slider_value_changed(value):
    #         print(f"Slider value changed: {value}")
    #         real_val = value * step
    #         value_label.setText(f"{real_val:.1f}")
    #         input_field.setText(f"{real_val:.1f}")
    #         self.update_value(target_list, real_val)

    def on_text_changed(self, text: str):
        """When the user types in the line edit, move the slider accordingly."""
        try:
            typed_val = float(text)
            if typed_val < self.min_val:
                typed_val = self.min_val
            elif typed_val > self.max_val:
                typed_val = self.max_val

            slider_pos = int(typed_val / self.step)
            self.slider.setValue(slider_pos)
        except ValueError:
            pass

    def set_value(self, new_val: float):
        """
        Programmatically set the slider and line edit to a new value.
        This is what you'd call when resetting to defaults, for example.
        """
        # Clamp to [min_val, max_val]
        if new_val < self.min_val:
            new_val = self.min_val
        elif new_val > self.max_val:
            new_val = self.max_val

        slider_pos = int(new_val / self.step)
        self.slider.setValue(slider_pos)  # triggers on_slider_changed
        # or you can forcibly set line_edit here as well, but on_slider_changed does it.

    def current_value(self) -> float:
        """Return the current numeric value, e.g. for saving config."""
        return float(self.line_edit.text())
