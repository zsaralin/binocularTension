import pyglet
import pyrealsense2 as rs
import numpy as np
from pyglet.gl import gl

# Configure the RealSense pipeline
pipeline = rs.pipeline()
config = rs.config()

# Enable the RGB stream
config.enable_stream(rs.stream.color, 640, 480, rs.format.rgb8, 30)

# Start streaming from the RealSense camera
pipeline.start(config)

# Create a Pyglet window
window = pyglet.window.Window(width=640, height=480, caption="RealSense RGB Camera Feed")

# Initialize texture to store camera feed
image_data = None

# Function to convert RealSense frame to Pyglet ImageData
def convert_frame_to_image_data(color_frame):
    frame_data = np.asanyarray(color_frame.get_data())  # Extract frame data as numpy array
    # Convert to Pyglet ImageData format (RGB format expected)
    return pyglet.image.ImageData(640, 480, 'RGB', frame_data.tobytes(), pitch=-640*3)

@window.event
def on_draw():
    global image_data
    window.clear()

    # Get frames from RealSense
    frames = pipeline.wait_for_frames()
    color_frame = frames.get_color_frame()

    if not color_frame:
        return

    # Convert the color frame to Pyglet ImageData
    image_data = convert_frame_to_image_data(color_frame)

    # Draw the image
    image_data.blit(0, 0, width=window.width, height=window.height)

def update(dt):
    pass

# Set up Pyglet's clock to call update regularly
pyglet.clock.schedule_interval(update, 1/30)  # 30 frames per second

# Start the Pyglet application loop
try:
    pyglet.app.run()
finally:
    # Stop the pipeline when exiting
    pipeline.stop()
