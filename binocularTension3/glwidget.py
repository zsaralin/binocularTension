import sys
import math
import numpy as np
import pyrealsense2 as rs
from PyQt5.QtWidgets import QOpenGLWidget  # Import QOpenGLWidget directly

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QOpenGLWindow
from PyQt5.QtCore import QTimer
import OpenGL.GL as gl
import cv2

import sys
import math
import ctypes
import numpy as np
import pyrealsense2 as rs
from PyQt5 import QtCore, QtWidgets, QtGui, QtOpenGL
from OpenGL import GL, GLU
import sys
import math
import numpy as np
import pyrealsense2 as rs
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QOpenGLWidget
from OpenGL import GL, GLU


def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = (
        b * c,
        a * d,
        a * c,
        a * b,
        b * d,
        c * d,
    )
    return np.array(
        [
            [aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
            [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
            [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc],
        ]
    )


class AppState:
    def __init__(self):
        # Initialize in degrees since OpenGL expects degrees for rotations
        self.pitch, self.yaw = -10.0, -15.0
        self.translation = np.array([0.0, 0.0, 1.0], np.float32)
        self.distance = 2.0
        self.mouse_btns = [False, False, False]
        self.paused = False
        self.decimate = 0
        self.scale = True
        self.attenuation = False
        self.color = True
        self.lighting = False
        self.postprocessing = False
        self.mouse_pos = None

    def reset(self):
        self.pitch, self.yaw, self.distance = 0.0, 0.0, 2.0
        self.translation[:] = 0.0, 0.0, 1.0

    @property
    def rotation(self):
        Rx = rotation_matrix((1, 0, 0), math.radians(-self.pitch))
        Ry = rotation_matrix((0, 1, 0), math.radians(-self.yaw))
        return np.dot(Ry, Rx).astype(np.float32)


class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.setMinimumSize(800, 600)
        self.state = AppState()

        # Configure RealSense pipeline
        self.pipeline = rs.pipeline()
        self.config = rs.config()

        # Check for a compatible device
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = self.config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()

        found_rgb = False
        for s in device.sensors:
            if s.get_info(rs.camera_info.name) == 'RGB Camera':
                found_rgb = True
                break
        if not found_rgb:
            print("The demo requires Depth camera with Color sensor")
            sys.exit(0)

        self.config.enable_stream(rs.stream.depth, rs.format.z16, 30)
        self.other_stream, self.other_format = rs.stream.color, rs.format.rgb8
        self.config.enable_stream(self.other_stream, self.other_format, 30)

        # Start streaming
        self.pipeline.start(self.config)
        profile = self.pipeline.get_active_profile()

        depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
        self.depth_intrinsics = depth_profile.get_intrinsics()
        self.w, self.h = self.depth_intrinsics.width, self.depth_intrinsics.height

        # Processing blocks
        self.pc = rs.pointcloud()
        self.decimate_filter = rs.decimation_filter()
        self.decimate_filter.set_option(rs.option.filter_magnitude, 2 ** self.state.decimate)
        self.colorizer = rs.colorizer()
        self.filters = [
            rs.disparity_transform(),
            rs.spatial_filter(),
            rs.temporal_filter(),
            rs.disparity_transform(False),
        ]

        self.other_profile = rs.video_stream_profile(profile.get_stream(self.other_stream))
        self.color_intrinsics = self.other_profile.get_intrinsics()
        self.color_w, self.color_h = self.color_intrinsics.width, self.color_intrinsics.height

        if self.state.color:
            self.image_w, self.image_h = self.color_w, self.color_h
        else:
            self.image_w, self.image_h = self.w, self.h

        self.image = np.zeros((self.image_h, self.image_w, 3), dtype=np.uint8)
        self.vertices = None
        self.texcoords = None

        # Set up timer to update frames
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update at ~30 FPS

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def initializeGL(self):
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glEnable(GL.GL_POINT_SPRITE)
        GL.glEnable(GL.GL_PROGRAM_POINT_SIZE)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        self.texture = GL.glGenTextures(1)

        if self.state.lighting:
            GL.glEnable(GL.GL_LIGHTING)
            GL.glEnable(GL.GL_LIGHT0)
            GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, [0.5, 0.5, 0.5, 0.0])
            GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
            GL.glLightfv(GL.GL_LIGHT0, GL.GL_AMBIENT, [0.75, 0.75, 0.75, 1.0])

    def resizeGL(self, w, h):
        GL.glViewport(0, 0, w, h)
        self.aspect_ratio = w / float(h) if h > 0 else 1.0

    def paintGL(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Set Projection
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GLU.gluPerspective(60.0, self.aspect_ratio, 0.01, 20.0)

        # Set ModelView
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        GLU.gluLookAt(0, 0, 0, 0, 0, 1, 0, -1, 0)

        # Apply Transformations
        GL.glTranslatef(0.0, 0.0, self.state.distance)
        GL.glRotatef(self.state.pitch, 1.0, 0.0, 0.0)
        GL.glRotatef(self.state.yaw, 0.0, 1.0, 0.0)

        # Apply Additional Custom Transformations (as in original Pyglet code)
        GL.glRotatef(-50.0, 1.0, 0.0, 0.0)  # Custom rotation on x-axis
        GL.glTranslatef(0.0, -2.0, 0.0)     # Custom translation
        GL.glTranslatef(0.0, 0.0, -self.state.distance)
        GL.glTranslatef(*self.state.translation)

        # Draw Axes if any mouse button is pressed
        if any(self.state.mouse_btns):
            self.draw_axes(0.1, 4)

        # Set Point Size and Attenuation
        psz = max(self.width(), self.height()) / float(max(self.w, self.h)) if self.state.scale else 1.0
        GL.glPointSize(psz)
        distance = [0.0, 0.0, 1.0] if self.state.attenuation else [1.0, 0.0, 0.0]
        GL.glPointParameterfv(GL.GL_POINT_DISTANCE_ATTENUATION, distance)

        # Set Lighting if enabled
        if self.state.lighting:
            ldir = np.dot(self.state.rotation, (0.5, 0.5, 0.5))  # Directional light
            ldir = list(ldir) + [0.0]  # w=0, directional light
            GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, ldir)
            GL.glEnable(GL.GL_LIGHTING)
            GL.glEnable(GL.GL_LIGHT0)
        else:
            GL.glDisable(GL.GL_LIGHTING)
            GL.glDisable(GL.GL_LIGHT0)

        # Bind Texture
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

        # Set Texture Parameters
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)

        # Upload Texture Data
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGB,
            self.image_w,
            self.image_h,
            0,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            self.image,
        )

        # Render Point Cloud
        if self.vertices is not None and self.texcoords is not None:
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glVertexPointer(3, GL.GL_FLOAT, 0, self.vertices)

            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, self.texcoords)

            GL.glDrawArrays(GL.GL_POINTS, 0, len(self.vertices) // 3)

            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glDisable(GL.GL_TEXTURE_2D)

        # Draw the Frustum and Axes
        GL.glColor3f(0.25, 0.25, 0.25)
        self.draw_frustum(self.depth_intrinsics)
        self.draw_axes()

        # Draw the 3D Green Cube **after** the Point Cloud
        GL.glColor3f(0.0, 1.0, 0.0)  # Ensure the cube is green
        GL.glPushMatrix()
        self.draw_green_cube()
        GL.glPopMatrix()

    def update_frame(self):
        if self.state.paused:
            return

        try:
            frames = self.pipeline.wait_for_frames()
        except RuntimeError:
            return

        depth_frame = frames.get_depth_frame().as_video_frame()
        other_frame = frames.first(self.other_stream).as_video_frame()

        depth_frame = self.decimate_filter.process(depth_frame)

        if self.state.postprocessing:
            for f in self.filters:
                depth_frame = f.process(depth_frame)

        # Grab new intrinsics (may be changed by decimation)
        self.depth_intrinsics = rs.video_stream_profile(depth_frame.profile).get_intrinsics()
        self.w, self.h = self.depth_intrinsics.width, self.depth_intrinsics.height

        color_image = np.asanyarray(other_frame.get_data())

        colorized_depth = self.colorizer.colorize(depth_frame)
        depth_colormap = np.asanyarray(colorized_depth.get_data())

        if self.state.color:
            mapped_frame, color_source = other_frame, color_image
            self.image_w, self.image_h = self.color_w, self.color_h
        else:
            mapped_frame, color_source = colorized_depth, depth_colormap
            self.image_w, self.image_h = self.w, self.h

        self.pc.map_to(mapped_frame)
        points = self.pc.calculate(depth_frame)

        # Handle color source or size change
        self.image = color_source

        # Retrieve vertices and texture coordinates
        verts = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)
        texcoords = np.asanyarray(points.get_texture_coordinates()).view(np.float32).reshape(-1, 2)

        # Convert texture coordinates to OpenGL format (flipped vertically)
        texcoords[:, 1] = 1.0 - texcoords[:, 1]

        self.vertices = verts.astype(np.float32)
        self.texcoords = texcoords.astype(np.float32)

        # Optionally, handle lighting normals if needed
        # (Not implemented here)

        self.update()  # Trigger repaint

    def draw_axes(self, size=1.0, width=2.0):
        GL.glLineWidth(width)
        GL.glBegin(GL.GL_LINES)
        # X axis (red)
        GL.glColor3f(1.0, 0.0, 0.0)
        GL.glVertex3f(0.0, 0.0, 0.0)
        GL.glVertex3f(size, 0.0, 0.0)
        # Y axis (green)
        GL.glColor3f(0.0, 1.0, 0.0)
        GL.glVertex3f(0.0, 0.0, 0.0)
        GL.glVertex3f(0.0, size, 0.0)
        # Z axis (blue)
        GL.glColor3f(0.0, 0.0, 1.0)
        GL.glVertex3f(0.0, 0.0, 0.0)
        GL.glVertex3f(0.0, 0.0, size)
        GL.glEnd()

    def draw_frustum(self, intrinsics):
        # Simple frustum drawing based on intrinsics
        GL.glBegin(GL.GL_LINES)
        GL.glColor3f(1.0, 1.0, 1.0)
        scale = 0.1  # Adjust scale as needed
        fov_x = math.degrees(2 * math.atan(intrinsics.fx / intrinsics.width))
        fov_y = math.degrees(2 * math.atan(intrinsics.fy / intrinsics.height))
        # Define frustum corners at a certain depth
        z = scale
        x = z * math.tan(math.radians(fov_x / 2))
        y = z * math.tan(math.radians(fov_y / 2))
        # Four corners
        corners = [
            (-x, -y, z),
            (x, -y, z),
            (x, y, z),
            (-x, y, z),
        ]
        # Connect to camera origin
        for corner in corners:
            GL.glVertex3f(0.0, 0.0, 0.0)
            GL.glVertex3f(*corner)
        # Connect the corners to form a rectangle
        for i in range(4):
            GL.glVertex3f(*corners[i])
            GL.glVertex3f(*corners[(i + 1) % 4])
        GL.glEnd()

    def draw_green_cube(self):
        """Draw a green cube positioned between the frustum and the point cloud."""
        cube_size = 0.5  # Adjust as needed
        cube_depth = 0.75  # Adjust to position between frustum and point cloud
        half_size = cube_size / 2.0

        vertices = [
            # Front face
            -half_size, -half_size, cube_depth + half_size,
             half_size, -half_size, cube_depth + half_size,
             half_size,  half_size, cube_depth + half_size,
            -half_size,  half_size, cube_depth + half_size,
            # Back face
            -half_size, -half_size, cube_depth - half_size,
             half_size, -half_size, cube_depth - half_size,
             half_size,  half_size, cube_depth - half_size,
            -half_size,  half_size, cube_depth - half_size,
        ]

        indices = [
            0, 1, 2, 3,  # Front face
            4, 5, 6, 7,  # Back face
            0, 1, 5, 4,  # Bottom face
            2, 3, 7, 6,  # Top face
            1, 2, 6, 5,  # Right face
            0, 3, 7, 4,  # Left face
        ]

        colors = [
            0.0, 1.0, 0.0,  # Green
            0.0, 1.0, 0.0,  # Green
            0.0, 1.0, 0.0,  # Green
            0.0, 1.0, 0.0,  # Green
            0.0, 1.0, 0.0,  # Green
            0.0, 1.0, 0.0,  # Green
            0.0, 1.0, 0.0,  # Green
            0.0, 1.0, 0.0,  # Green
        ]

        # Enable client states
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)

        # Convert lists to ctypes arrays
        vertex_data = (GL.GLfloat * len(vertices))(*vertices)
        color_data = (GL.GLfloat * len(colors))(*colors)
        index_data = (GL.GLuint * len(indices))(*indices)

        # Set pointers
        GL.glVertexPointer(3, GL.GL_FLOAT, 0, vertex_data)
        GL.glColorPointer(3, GL.GL_FLOAT, 0, color_data)

        # Draw the cube using GL_QUADS
        GL.glDrawElements(GL.GL_QUADS, len(indices), GL.GL_UNSIGNED_INT, index_data)

        # Disable client states
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_COLOR_ARRAY)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.state.mouse_btns[0] = True
        elif event.button() == QtCore.Qt.RightButton:
            self.state.mouse_btns[1] = True
        elif event.button() == QtCore.Qt.MiddleButton:
            self.state.mouse_btns[2] = True
        self.state.mouse_pos = (event.x(), event.y())

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.state.mouse_btns[0] = False
        elif event.button() == QtCore.Qt.RightButton:
            self.state.mouse_btns[1] = False
        elif event.button() == QtCore.Qt.MiddleButton:
            self.state.mouse_btns[2] = False

    def mouseMoveEvent(self, event):
        if self.state.mouse_pos is None:
            self.state.mouse_pos = (event.x(), event.y())
            return
        dx = event.x() - self.state.mouse_pos[0]
        dy = event.y() - self.state.mouse_pos[1]
        self.state.mouse_pos = (event.x(), event.y())

        if self.state.mouse_btns[0]:
            self.state.yaw += dx * 0.5
            self.state.pitch += dy * 0.5
        elif self.state.mouse_btns[1]:
            self.state.translation[0] += dx * 0.01
            self.state.translation[1] -= dy * 0.01
        elif self.state.mouse_btns[2]:
            self.state.distance += dy * 0.01

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120  # 1 unit per notch
        self.state.distance -= delta * 0.1

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_R:
            self.state.reset()
        elif key == QtCore.Qt.Key_P:
            self.state.paused = not self.state.paused
        elif key == QtCore.Qt.Key_Escape:
            self.close()
        elif key == QtCore.Qt.Key_D:
            self.state.decimate = (self.state.decimate + 1) % 4  # Example cycle
            self.decimate_filter.set_option(rs.option.filter_magnitude, 2 ** self.state.decimate)
        elif key == QtCore.Qt.Key_Z:
            self.state.scale = not self.state.scale
        elif key == QtCore.Qt.Key_X:
            self.state.attenuation = not self.state.attenuation
        elif key == QtCore.Qt.Key_C:
            self.state.color = not self.state.color
            # Reconfigure streams if color source toggled
            self.pipeline.stop()
            self.pipeline.start(self.config)
        elif key == QtCore.Qt.Key_L:
            self.state.lighting = not self.state.lighting
            if self.state.lighting:
                GL.glEnable(GL.GL_LIGHTING)
                GL.glEnable(GL.GL_LIGHT0)
            else:
                GL.glDisable(GL.GL_LIGHTING)
                GL.glDisable(GL.GL_LIGHT0)
        elif key == QtCore.Qt.Key_F:
            self.state.postprocessing = not self.state.postprocessing
        elif key == QtCore.Qt.Key_S:
            # Save PNG functionality (not implemented here)
            pass
        elif key == QtCore.Qt.Key_E:
            # Export to PLY functionality (not implemented here)
            pass

    def closeEvent(self, event):
        self.pipeline.stop()
        event.accept()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("RealSense Viewer")
        self.glWidget = GLWidget(self)

        # Create buttons and other UI elements
        self.button_pause = QtWidgets.QPushButton("Pause/Resume", self)
        self.button_pause.clicked.connect(self.toggle_pause)

        self.button_reset = QtWidgets.QPushButton("Reset View", self)
        self.button_reset.clicked.connect(self.glWidget.state.reset)

        # Layout the widgets
        centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(centralWidget)

        layout = QtWidgets.QVBoxLayout()
        centralWidget.setLayout(layout)

        layout.addWidget(self.glWidget)

        # Add a horizontal layout for buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.button_pause)
        button_layout.addWidget(self.button_reset)

        layout.addLayout(button_layout)

    def toggle_pause(self):
        self.glWidget.state.paused = not self.glWidget.state.paused


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
