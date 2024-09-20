import pyrealsense2 as rs
import numpy as np
import cv2
from flask import Flask, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS to prevent security issues

# Setup for both cameras
pipeline0 = rs.pipeline()
config0 = rs.config()
config0.enable_device('213622253034')  # Camera 0 serial number
# Set resolution to 1280x800 @ 30 FPS for Camera 0
config0.enable_stream(rs.stream.color, 1280, 800, rs.format.bgr8, 30)
pipeline0.start(config0)

pipeline1 = rs.pipeline()
config1 = rs.config()
config1.enable_device('213622252175')  # Camera 1 serial number
# Set resolution to 1280x800 @ 30 FPS for Camera 1
config1.enable_stream(rs.stream.color, 1280, 800, rs.format.bgr8, 30)
pipeline1.start(config1)

# Function to generate frames from Camera 0
def gen_frames_camera0():
    while True:
        frames = pipeline0.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        color_image = np.asanyarray(color_frame.get_data())
        ret, buffer = cv2.imencode('.jpg', color_image)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Function to generate frames from Camera 1
def gen_frames_camera1():
    while True:
        frames = pipeline1.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue
        color_image = np.asanyarray(color_frame.get_data())
        ret, buffer = cv2.imencode('.jpg', color_image)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Flask routes to stream video from both cameras
@app.route('/video_feed_0')
def video_feed_0():
    return Response(gen_frames_camera0(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_1')
def video_feed_1():
    return Response(gen_frames_camera1(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
