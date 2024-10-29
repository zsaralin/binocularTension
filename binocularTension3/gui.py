import pyglet
import imgui
from imgui.integrations.pyglet import PygletRenderer
import json
import os

window = pyglet.window.Window(800, 600, "Control Panel Example with Pyglet + ImGui")
imgui.create_context()
impl = PygletRenderer(window)

# Load config from file or return defaults if the file doesn't exist
def load_config():
    if os.path.exists('config.json'):
        with open('config.json', 'r') as config_file:
            return json.load(config_file)
    else:
        return {
            "rotate_x": 0,
            "rotate_y": 0,
            "rotate_z": 0,
            "translate_x": 0,
            "translate_y": 0,
            "translate_z": 0,
            "x_threshold": 5.0,
            "y_threshold": 5.0,
            "z_threshold": 1.4,
        }

config = load_config()

# Variables for rotation, translation, and thresholds
rotation = [config['rotate_x'], config['rotate_y'], config['rotate_z']]
translation = [config['translate_x'], config['translate_y'], config['translate_z']]
thresholds = [
    config['x_threshold'], config['y_threshold'], config['z_threshold']
]

def save_config():
    config = {
        "rotate_x": rotation[0],
        "rotate_y": rotation[1],
        "rotate_z": rotation[2],
        "translate_x": translation[0],
        "translate_y": translation[1],
        "translate_z": translation[2],
        "x_threshold": thresholds[0],
        "y_threshold": thresholds[1],
        "z_threshold": thresholds[2],
    }
    
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)
    print("Config saved to config.json")

@window.event
def on_draw():
    global rotation, translation, thresholds
    
    window.clear()
    imgui.new_frame()

    # Rotation Sliders
    imgui.begin("Control Panel")
    imgui.text("Rotation (degrees)")
    changed_rot_x, rotation[0] = imgui.slider_int("Rot X", int(rotation[0]), -180, 180)
    changed_rot_y, rotation[1] = imgui.slider_int("Rot Y", int(rotation[1]), -180, 180)
    changed_rot_z, rotation[2] = imgui.slider_int("Rot Z", int(rotation[2]), -180, 180)

    # Translation Sliders
    imgui.text("Translation (meters)")
    changed_trans_x, translation[0] = imgui.slider_int("Trans X", int(translation[0]), -3000, 3000)
    changed_trans_y, translation[1] = imgui.slider_int("Trans Y", int(translation[1]), -3000, 3000)
    changed_trans_z, translation[2] = imgui.slider_int("Trans Z", int(translation[2]), -3000, 3000)

    # Threshold Sliders
    imgui.text("Thresholds")
    changed_x_thresh, thresholds[0] = imgui.slider_int("X Threshold", int(thresholds[0]), 0, 1600)
    changed_y_thresh, thresholds[1] = imgui.slider_int("Y Threshold", int(thresholds[1]), 0, 1600)
    changed_z_thresh, thresholds[2] = imgui.slider_int("Z Threshold", int(thresholds[2]), 0, 1600)

    # Save button
    if imgui.button("Save Config"):
        save_config()

    imgui.end()

    # Render ImGui
    imgui.render()
    impl.render(imgui.get_draw_data())

@window.event
def on_close():
    impl.shutdown()
    window.close()

pyglet.app.run()
