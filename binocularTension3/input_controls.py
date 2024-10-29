import numpy as np
import pyglet
import pyrealsense2 as rs
# Mouse control functions
def handle_mouse_drag(x, y, dx, dy, buttons, modifiers, state, window):
    """Handle mouse dragging for rotation and translation."""
    w, h = map(float, window.get_size())  # Get the size from the window instance

    if buttons & pyglet.window.mouse.LEFT:
        state.yaw -= dx * 0.5
        state.pitch -= dy * 0.5

    if buttons & pyglet.window.mouse.RIGHT:
        dp = np.array((dx / w, -dy / h, 0), np.float32)
        state.translation += np.dot(state.rotation, dp)

    if buttons & pyglet.window.mouse.MIDDLE:
        dz = dy * 0.01
        state.translation -= (0, 0, dz)
        state.distance -= dz

def handle_mouse_btns(x, y, button, modifiers, state):
    """Handle mouse button presses."""
    state.mouse_btns[0] ^= (button & pyglet.window.mouse.LEFT)
    state.mouse_btns[1] ^= (button & pyglet.window.mouse.RIGHT)
    state.mouse_btns[2] ^= (button & pyglet.window.mouse.MIDDLE)

def handle_mouse_scroll(x, y, scroll_x, scroll_y, state):
    """Handle mouse scrolling for zoom."""
    dz = scroll_y * 0.1
    state.translation -= (0, 0, dz)
    state.distance -= dz

# Keyboard control functions
def handle_key_press(symbol, modifiers, state, decimate, window):
    """Handle keyboard presses for various controls."""
    if symbol == pyglet.window.key.R:
        state.reset()

    if symbol == pyglet.window.key.P:
        state.paused ^= True

    if symbol == pyglet.window.key.D:
        state.decimate = (state.decimate + 1) % 3
        decimate.set_option(rs.option.filter_magnitude, 2 ** state.decimate)

    if symbol == pyglet.window.key.C:
        state.color ^= True

    if symbol == pyglet.window.key.Z:
        state.scale ^= True

    if symbol == pyglet.window.key.X:
        state.attenuation ^= True

    if symbol == pyglet.window.key.L:
        state.lighting ^= True

    if symbol == pyglet.window.key.F:
        state.postprocessing ^= True

    if symbol == pyglet.window.key.S:
        pyglet.image.get_buffer_manager().get_color_buffer().save('out.png')

    if symbol == pyglet.window.key.Q:
        window.close()
