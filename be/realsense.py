import pyrealsense2 as rs
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import QMessageBox
import numpy as np
import cv2
import socket
import threading
from detection_data import DetectionData

class RealSenseManager(QObject):
    camera_disconnected = pyqtSignal()  # Signal to notify disconnection

    def __init__(self, server_host="localhost", server_port=12345):
        super().__init__()
        self.pipeline = rs.pipeline()
        config = rs.config()

        # Enable streams
        config.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 60)
        config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 60)
        config.enable_stream(rs.stream.infrared, 1, 848, 480, rs.format.y8, 60)

        self.initialized = False  # Track if camera started successfully

        try:
            self.pipeline_profile = self.pipeline.start(config)
            self.initialized = True  # Camera started successfully
        except RuntimeError:
            self.initialized = False  # Camera failed to start
            self.camera_disconnected.emit()  # Notify UI
            return  # Exit initialization without crashing

        # Initialize align object to align depth to color
        self.align = rs.align(rs.stream.color)

        self.color_frame = None
        self.depth_frame = None
        self.infrared_frame = None
        self.brightness_threshold = 100  # Brightness threshold for switching to infrared

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frames)
        self.timer.start(30)  # Approximately 30 FPS

        self.detection_data = DetectionData()
        self.camera_connected = True  # Flag to track camera status

        # Start the server
        self.server_host = server_host
        self.server_port = server_port
        self.server_running = True
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()

    def update_frames(self):
        """Fetch and process frames, detect camera disconnection."""
        if not self.initialized:
            return  # Skip processing if camera is not initialized
        try:
            frames = self.pipeline.wait_for_frames(timeout_ms=5000)  # Timeout ensures detection of disconnection

            # Align depth to color
            aligned_frames = self.align.process(frames)

            self.color_frame = aligned_frames.get_color_frame()
            self.depth_frame = aligned_frames.get_depth_frame()
            self.infrared_frame = frames.get_infrared_frame()

            if not self.color_frame or not self.depth_frame:
                return  # Skip frame if either is missing

            # Reset camera disconnection flag (camera is active)
            self.camera_connected = True  

            # Check brightness of color frame
            color_image = np.asanyarray(self.color_frame.get_data())
            brightness = np.mean(cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY))

            # Use infrared frame as color if brightness is below threshold
            if brightness < self.brightness_threshold:
                self.detection_data.set_is_dark(True)
                self.color_frame = self.infrared_frame
            else:
                self.detection_data.set_is_dark(False)

        except RuntimeError:
            if self.camera_connected:  # Show error popup only once per disconnection
                self.camera_connected = False  # Mark as disconnected
                self.camera_disconnected.emit()  # Notify MainWindow
                self.stop()  # Stop the pipeline to avoid further errors

    def get_color_frame(self):
        return self.color_frame  # Returns either color or infrared frame as a pyrealsense2 frame

    def get_depth_frame(self):
        return self.depth_frame

    def get_depth_intrinsics(self):
        """Retrieve depth intrinsics (necessary for 2D to 3D projection)."""
        depth_stream = self.pipeline_profile.get_stream(rs.stream.depth)  # Fetch depth stream profile
        intrinsics = depth_stream.as_video_stream_profile().get_intrinsics()
        return intrinsics

    def get_depth_scale(self):
        """Retrieve the depth scale for converting depth values to meters."""
        depth_sensor = self.pipeline_profile.get_device().first_depth_sensor()
        return depth_sensor.get_depth_scale()

    def stop(self):
        """Stop the pipeline safely and close the server."""
        try:
            self.pipeline.stop()
        except RuntimeError:
            pass  # Ignore errors if already stopped

        self.server_running = False  # Stop server thread
        try:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((self.server_host, self.server_port))
        except Exception:
            pass  # Ignore errors when closing

    ### 🖥️ SERVER SOCKET FOR CAMERA STATUS ###
    def start_server(self):
        """Start a server socket to allow frontend to check camera connection status."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind((self.server_host, self.server_port))
            server_socket.listen(5)
            print(f"Server running at {self.server_host}:{self.server_port}...")

            while self.server_running:
                client_socket, addr = server_socket.accept()
                with client_socket:
                    # Respond with camera connection status
                    status = "connected" if self.camera_connected else "disconnected"
                    client_socket.sendall(status.encode())
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            server_socket.close()
