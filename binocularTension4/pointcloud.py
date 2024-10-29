import sys
import math
import numpy as np
import pyrealsense2 as rs
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QSurfaceFormat
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QWidget, QHBoxLayout
from pointcloud_drawing_utils import draw_vertical_dividers,draw_horizontal_dividers, draw_keypoints, draw_movement_points, draw_depth_plane
import cv2
from detection_data import DetectionData
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLU import gluNewQuadric, gluSphere
from transformation_utils import apply_dynamic_transformation
from headpoint_utils import compute_general_head_points, compute_movement_points
from active_movement_logic import update_active_movement
from cube_utils.cube_manager import CubeManager
from live_config import LiveConfig

class AppState:

    def __init__(self, *args, **kwargs):
        self.pitch, self.yaw = 0,0  # Degrees
        self.translation = np.array([0, 0, 0], dtype=np.float32)
        self.mouse_btns = [False, False, False]
        self.prev_mouse = 0, 0
        self.decimate = 1
        self.scale = True
        self.color = True
        self.paused = False

    def reset(self):
        self.pitch, self.yaw = 0, 0
        self.translation[:] = 0, 0, 0

state = AppState()
import numpy as np


class GLWidget(QGLWidget):
    def __init__(self, rs_manager, parent=None):
        super(GLWidget, self).__init__(parent)

        self.setFocusPolicy(Qt.StrongFocus)  # Ensure GLWidget can capture key events
        self.setFocus()  # Set initial focus on the widget

        self.rs_manager = rs_manager
        self.detection_data = DetectionData()  # Initialize detection data
        self.cube_manager = CubeManager.get_instance()

        # Processing blocks
        self.pc = rs.pointcloud()
        self.decimate = rs.decimation_filter()
        self.decimate.set_option(rs.option.filter_magnitude, 2 ** state.decimate)
        self.colorizer = rs.colorizer()

        # Timer for updating frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)  # Approximately 30 FPS

        # Attributes for vertices and colors
        self.vertices = None
        self.colors = None

        # Instance of LiveConfig for live configuration settings
        self.live_config = LiveConfig.get_instance()

        # Attributes for storing the last frame's transformed headpoints, movement points, and active movement
        self.headpoints_transformed = None
        self.movement_points_transformed = None
        self.active_movement_id = None
        self.active_movement_type = None

        


    def initializeGL(self):
        glClearColor(0, 0, 0, 1)
        glEnable(GL_DEPTH_TEST)
        glPointSize(2)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        aspect = w / h if h > 0 else 1
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, aspect, 0.01, 100.0)
        glMatrixMode(GL_MODELVIEW)
        

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(*state.translation)
        glRotatef(state.pitch, 1, 0, 0)
        glRotatef(state.yaw, 0, 1, 0)

        # Clear and load identity only if not paused
        if not state.paused:
            # Update vertices, colors, and additional elements only if not paused
            depth_frame = self.rs_manager.get_depth_frame()
            color_frame = self.rs_manager.get_color_frame()
            if depth_frame and color_frame:
                self.pc.map_to(color_frame)
                points = self.pc.calculate(depth_frame)

                v, t = points.get_vertices(), points.get_texture_coordinates()
                verts = np.asanyarray(v).view(np.float32).reshape(-1, 3)
                texcoords = np.asanyarray(t).view(np.float32).reshape(-1, 2)
                verts[:, 0] *= -1  # Flip the X-axis for the mirror effect

                verts[:, 2] *= -1  # Invert Z-axis for OpenGL's coordinate system
                verts[:, 1] *= -1  # Invert Y-axis for OpenGL's coordinate system

                rotation = [self.live_config.rotate_x, self.live_config.rotate_y, self.live_config.rotate_z]
                translation = [self.live_config.translate_x, self.live_config.translate_y, self.live_config.translate_z]

                transformed_verts = apply_dynamic_transformation(verts, rotation, translation)

                color_image = np.asanyarray(color_frame.get_data())
                color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)  # Convert from BGR to RGB

                h, w, _ = color_image.shape

                texcoords[:, 0] *= w
                texcoords[:, 1] *= h
                texcoords = texcoords.astype(int)
                np.clip(texcoords[:, 0], 0, w - 1, out=texcoords[:, 0])
                np.clip(texcoords[:, 1], 0, h - 1, out=texcoords[:, 1])

                colors = color_image[texcoords[:, 1], texcoords[:, 0]]
                self.vertices = transformed_verts  
                self.colors = colors / 255.0  # Normalize colors

                # Compute and store transformed elements for re-drawing when paused
                persons_with_ids = self.detection_data.get_persons_with_ids()
                non_person_movement_boxes = self.detection_data.get_non_person_movement_boxes()
                person_moving_status = self.detection_data.get_person_moving_status()
                
                intrinsics = self.rs_manager.get_depth_intrinsics()  # Get RealSense intrinsics for depth calculations
                depth_image = np.asanyarray(depth_frame.get_data())
                depth_scale = self.rs_manager.get_depth_scale()  # Scale for converting depth value to meters
                draw_keypoints(persons_with_ids, intrinsics, depth_image, depth_scale, rotation, translation)
                self.headpoints_transformed = compute_general_head_points(
                    persons_with_ids, intrinsics, depth_image, depth_scale, rotation, translation
                )
                self.movement_points_transformed = compute_movement_points(
                    non_person_movement_boxes, intrinsics, depth_image, depth_scale, rotation, translation
                )
                self.active_movement_id, self.active_movement_type = update_active_movement(
                    self.headpoints_transformed, person_moving_status, self.movement_points_transformed,
                    image_width=640, image_height=480, intrinsics=intrinsics
                )

                self.detection_data.set_active_movement_id(self.active_movement_id)
                self.detection_data.set_active_movement_type(self.active_movement_type)

        # Always render the stored vertices and colors
        if self.vertices is not None and self.colors is not None:
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_COLOR_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, self.vertices)
            glColorPointer(3, GL_FLOAT, 0, self.colors)
            glDrawArrays(GL_POINTS, 0, len(self.vertices))
            glDisableClientState(GL_VERTEX_ARRAY)
            glDisableClientState(GL_COLOR_ARRAY)
        if self.headpoints_transformed or self.movement_points_transformed:
        # Always re-draw stored headpoints, keypoints, and other elements
            draw_movement_points(self.headpoints_transformed, self.movement_points_transformed, self.active_movement_id, self.active_movement_type)
        draw_vertical_dividers()
        draw_horizontal_dividers()
        draw_depth_plane()
        self.cube_manager.draw_cubes()
            



    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            state.mouse_btns[0] = True
        elif event.button() == Qt.RightButton:
            state.mouse_btns[1] = True
        state.prev_mouse = event.x(), event.y()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            state.mouse_btns[0] = False
        elif event.button() == Qt.RightButton:
            state.mouse_btns[1] = False

    def mouseMoveEvent(self, event):
        dx = event.x() - state.prev_mouse[0]
        dy = event.y() - state.prev_mouse[1]

        if state.mouse_btns[0]:
            state.yaw += dx * 0.5
            state.pitch += dy * 0.5
        elif state.mouse_btns[1]:
            state.translation[0] += dx * 0.01
            state.translation[1] -= dy * 0.01

        state.prev_mouse = event.x(), event.y()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 120  # 1 unit per notch
        state.translation[2] += delta * 0.1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Q:
            self.close()
            self.pipeline.stop()
            QApplication.instance().quit()
        elif event.key() == Qt.Key_R:
            state.reset()
        elif event.key() == Qt.Key_P:
            state.paused ^= True
