"""
Usage:
------
Mouse:
    Drag with left button to rotate around pivot (thick small axes),
    with right button to translate and the wheel to zoom.


Keyboard:
    [p]     Pause
    [r]     Reset View
    [d]     Cycle through decimation values
    [z]     Toggle point scaling
    [x]     Toggle point distance attenuation
    [c]     Toggle color source
    [l]     Toggle lighting
    [f]     Toggle depth post-processing
    [s]     Save PNG (./out.png)
    [e]     Export points to ply (./out.ply)
    [q/ESC] Quit
"""
import cv2
from transform_utils import get_rotation_matrix
from drawing_utils import (
    draw_person_bounding_boxes,
    draw_movement_boxes,
    draw_keypoints_manually,
    draw_skeleton,
    KEYPOINT_CONNECTIONS,
    bbox_iou
)
from deep_sort_realtime.deepsort_tracker import DeepSort
import math
import ctypes
import pyglet
import pyglet.gl as gl
from pyglet.gl import glu  # Import glu from pyglet.gl
import numpy as np
import pyrealsense2 as rs
from input_controls import handle_mouse_btns, handle_key_press, handle_mouse_drag, handle_mouse_scroll
from scene_utils import frustum, axes, grid
from movement_detection import (
    detect_movement,
    get_non_person_movement_boxes
)
from ultralytics import YOLO


# https://stackoverflow.com/a/6802723
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
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])


class AppState:


    def __init__(self, *args, **kwargs):
        self.pitch, self.yaw = math.radians(-10), math.radians(-15)
        self.translation = np.array([0, 0, 1], np.float32)
        self.distance = 2
        self.mouse_btns = [False, False, False]
        self.paused = False
        self.decimate = 0
        self.scale = True
        self.attenuation = False
        self.color = True
        self.lighting = False
        self.postprocessing = True


    def reset(self):
        self.pitch, self.yaw, self.distance = 0, 0, 2
        self.translation[:] = 0, 0, 1


    @property
    def rotation(self):
        Rx = rotation_matrix((1, 0, 0), math.radians(-self.pitch))
        Ry = rotation_matrix((0, 1, 0), math.radians(-self.yaw))
        return np.dot(Ry, Rx).astype(np.float32)




state = AppState()


# Configure streams
pipeline = rs.pipeline()
config = rs.config()


pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()


found_rgb = False
for s in device.sensors:
    if s.get_info(rs.camera_info.name) == 'RGB Camera':
        found_rgb = True
        break
if not found_rgb:
    print("The demo requires Depth camera with Color sensor")
    exit(0)


config.enable_stream(rs.stream.depth, rs.format.z16, 60)
other_stream, other_format = rs.stream.color, rs.format.bgr8
config.enable_stream(other_stream, 640, 480, other_format, 60)


# Start streaming
pipeline.start(config)
profile = pipeline.get_active_profile()


depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
depth_intrinsics = depth_profile.get_intrinsics()
w, h = depth_intrinsics.width, depth_intrinsics.height


# Processing blocks
pc = rs.pointcloud()
decimate = rs.decimation_filter()
decimate.set_option(rs.option.filter_magnitude, 2 ** state.decimate)
colorizer = rs.colorizer()
filters = [rs.disparity_transform(),
           rs.spatial_filter(),
           rs.temporal_filter(),
           rs.disparity_transform(False)]




# pyglet
window = pyglet.window.Window(
    width=1280,  # Set the window width
    height=480,  # Set the window height
    config=gl.Config(
        double_buffer=True,
        samples=8,
    ),
    resizable=True, vsync=True)
keys = pyglet.window.key.KeyStateHandler()
window.push_handlers(keys)
# cp = ControlPanel()
# Initialize YOLO pose model
def initialize_yolo_model(model_path):
    pose_model = YOLO(model_path)
    pose_model.verbose = False  # Suppress logging
    return pose_model


# Initialize the Deep SORT tracker
def initialize_tracker():
    return DeepSort(max_age=5, n_init=3, nms_max_overlap=1.0, max_cosine_distance=0.2)


# Process YOLO-Pose results and prepare data for tracking
def process_pose_results(pose_results):
    keypoints_data = pose_results[0].keypoints.data.cpu().numpy() if len(pose_results[0].keypoints) > 0 else []
    boxes = pose_results[0].boxes.xyxy.cpu().numpy() if pose_results[0].boxes is not None else []
    confidences = pose_results[0].boxes.conf.cpu().numpy() if pose_results[0].boxes is not None else []
    detections = [
        ([int(x1), int(y1), int(x2) - int(x1), int(y2) - int(y1)], confidences[i], 'person')
        for i, (x1, y1, x2, y2) in enumerate(boxes)
    ]


    return keypoints_data, detections


# Update tracking using Deep SORT
def update_tracker(tracker, detections, color_image):
    tracks = tracker.update_tracks(detections, frame=color_image)
    if len(tracks) == 0:
        print("No tracks found, resetting tracker.")


        tracker = initialize_tracker()  # Reset tracker if no tracks found
    return tracker, tracks


pose_model = initialize_yolo_model("yolo/yolo11n-pose.pt")
tracker = initialize_tracker()
tracks = []
def convert_fmt(fmt):
    """rs.format to pyglet format string"""
    return {
        rs.format.rgb8: 'RGB',
        rs.format.bgr8: 'BGR',
        rs.format.rgba8: 'RGBA',
        rs.format.bgra8: 'BGRA',
        rs.format.y8: 'L',
    }[fmt]




# Create a VertexList to hold pointcloud data
# Will pre-allocate memory according to the attributes below
vertex_list = pyglet.graphics.vertex_list(
    w * h, 'v3f/stream', 't2f/stream', 'n3f/stream')
# Create and allocate memory for our color data
other_profile = rs.video_stream_profile(profile.get_stream(other_stream))


image_w, image_h = w, h
color_intrinsics = other_profile.get_intrinsics()
color_w, color_h = color_intrinsics.width, color_intrinsics.height


if state.color:
    image_w, image_h = color_w, color_h
image_data = pyglet.image.ImageData(image_w, image_h, convert_fmt(
other_profile.format()), (gl.GLubyte * (image_w * image_h * 3))())


if (pyglet.version <  '1.4' ):
    # pyglet.clock.ClockDisplay has been removed in 1.4
    fps_display = pyglet.clock.ClockDisplay()
else:
    fps_display = pyglet.window.FPSDisplay(window)




@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    handle_mouse_drag(x, y, dx, dy, buttons, modifiers, state, window)


window.on_mouse_press = lambda x, y, button, modifiers: handle_mouse_btns(x, y, button, modifiers, state)
window.on_mouse_release = lambda x, y, button, modifiers: handle_mouse_btns(x, y, button, modifiers, state)


@window.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    handle_mouse_scroll(x, y, scroll_x, scroll_y, state)


@window.event
def on_key_press(symbol, modifiers):
    handle_key_press(symbol, modifiers, state, decimate, window)




def draw_green_cube():
    """Draw a green cube positioned between the frustum and the point cloud."""
    # Define the size of the cube
    cube_size = 0.5  # Adjust as needed


    # Define the depth where the cube will be placed
    cube_depth = 0.75  # Adjust to position between frustum (near) and point cloud (far)


    # Calculate half size for convenience
    half_size = cube_size / 2


    # Define the 8 vertices of the cube
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


    # Define the color (green) for each vertex
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


    # Define the indices for the cube faces (using quads)
    indices = [
        0, 1, 2, 3,  # Front face
        4, 5, 6, 7,  # Back face
        0, 1, 5, 4,  # Bottom face
        2, 3, 7, 6,  # Top face
        1, 2, 6, 5,  # Right face
        0, 3, 7, 4   # Left face
    ]


    # Enable client states
    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
    gl.glEnableClientState(gl.GL_COLOR_ARRAY)


    # Convert lists to ctypes arrays
    vertex_data = (gl.GLfloat * len(vertices))(*vertices)
    color_data = (gl.GLfloat * len(colors))(*colors)
    index_data = (gl.GLuint * len(indices))(*indices)


    # Set pointers
    gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertex_data)
    gl.glColorPointer(3, gl.GL_FLOAT, 0, color_data)


    # Draw the cube using GL_QUADS
    gl.glDrawElements(gl.GL_QUADS, len(indices), gl.GL_UNSIGNED_INT, index_data)


    # Disable client states
    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
    gl.glDisableClientState(gl.GL_COLOR_ARRAY)




@window.event
def on_draw():
    window.clear()
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)  # Clear color and depth buffers


    # Retrieve framebuffer size for accurate pixel dimensions
    width, height = window.get_framebuffer_size()
    left_width = width // 2
    left_height = height
    # ----------------------------
    # 1. Render RGB Image on Left
    # ----------------------------
    gl.glViewport(0, 0, int(left_width), int(left_height))  # Set viewport to left half


    # Set up orthographic projection matching the viewport
    # gl.glMatrixMode(gl.GL_PROJECTION)
    # gl.glLoadIdentity()
    # glu.gluOrtho2D(0, left_width*2, 0, left_height)


    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glViewport(0, 0, int(left_width), int(left_height))  # Set viewport to left half
# Disable depth testing and lighting for 2D rendering
    gl.glDisable(gl.GL_DEPTH_TEST)
    gl.glDisable(gl.GL_LIGHTING)
    gl.glDisable(gl.GL_POINT_SPRITE)
    gl.glColor3f(1.0, 1.0, 1.0)  # White color
    # Get the RGB frame
    frames = pipeline.wait_for_frames()
    color_frame = frames.get_color_frame()


    # Convert color frame to numpy array
    color_image = np.asanyarray(color_frame.get_data())
    # color_image = color_image[:, :, ::-1]  # Convert BGR to RGB


    # Flip the color image vertically
    flipped_image = np.flipud(color_image)
    # Create Pyglet texture
    image_data = pyglet.image.ImageData(640, 480, convert_fmt(rs.format.bgr8), color_image.tobytes(), pitch=-640 * 3)
    texture = image_data.get_texture()
    texture.blit(0, 0, width=1280, height=480)


    # Restore depth testing for 3D rendering
    gl.glEnable(gl.GL_DEPTH_TEST)


    # -------------------------------
    # 2. Render Point Cloud on Right
    # -------------------------------
    # Define viewport dimensions (right half)
    right_x = left_width
    right_width = width - left_width
    right_height = height


    gl.glViewport(right_x, 0, right_width, right_height)


    # Set up perspective projection for 3D rendering
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    glu.gluPerspective(60, right_width / float(right_height), 0.01, 20)


    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()


    # Set up camera view
    glu.gluLookAt(0, 0, 0, 0, 0, 1, 0, -1, 0)


    gl.glTranslatef(0, 0, state.distance)
    gl.glRotated(state.pitch, 1, 0, 0)
    gl.glRotated(state.yaw, 0, 1, 0)
    gl.glRotatef(-50, 1, 0, 0)  # Custom rotation on x-axis
    gl.glTranslatef(0, -2, 0)    # Custom translation


    if any(state.mouse_btns):
        axes(0.1, 4)


    gl.glTranslatef(0, 0, -state.distance)
    gl.glTranslatef(*state.translation)


    gl.glColor3f(0.5, 0.5, 0.5)
    gl.glPushMatrix()
    gl.glTranslatef(0, 0.5, 0.5)
    gl.glPopMatrix()


    # Set point cloud rendering parameters
    psz = max(right_width, right_height) / float(max(w, h)) if state.scale else 1
    gl.glPointSize(psz)
    distance = (0, 0, 1) if state.attenuation else (1, 0, 0)
    gl.glPointParameterfv(gl.GL_POINT_DISTANCE_ATTENUATION,
                          (gl.GLfloat * 3)(*distance))


    if state.lighting:
        ldir = [0.5, 0.5, 0.5]  # World-space lighting
        ldir = np.dot(state.rotation, (0, 0, 1))  # MeshLab style lighting
        ldir = list(ldir) + [0]  # w=0, directional light
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, (gl.GLfloat * 4)(*ldir))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE,
                     (gl.GLfloat * 3)(1.0, 1.0, 1.0))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT,
                     (gl.GLfloat * 3)(0.75, 0.75, 0.75))
        gl.glEnable(gl.GL_LIGHT0)
        gl.glEnable(gl.GL_NORMALIZE)
        gl.glEnable(gl.GL_LIGHTING)


    # Render the point cloud
    gl.glColor3f(1, 1, 1)
    flip_image_data = pyglet.image.ImageData(640, 480, convert_fmt(rs.format.bgr8), flipped_image.tobytes(), pitch=-640 * 3)
    flip_texture = flip_image_data.get_texture()
    gl.glEnable(flip_texture.target)
    gl.glBindTexture(flip_texture.target, flip_texture.id)
    gl.glTexParameteri(
        gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)


    # Enable point sprite for textured points
    gl.glEnable(gl.GL_POINT_SPRITE)


    if not state.scale and not state.attenuation:
        gl.glDisable(gl.GL_MULTISAMPLE)  # For true 1px points with MSAA on
    vertex_list.draw(gl.GL_POINTS)
    gl.glDisable(flip_texture.target)
    if not state.scale and not state.attenuation:
        gl.glEnable(gl.GL_MULTISAMPLE)


    gl.glDisable(gl.GL_LIGHTING)


    # Draw the frustum and axes
    gl.glColor3f(0.25, 0.25, 0.25)
    frustum(depth_intrinsics)
    axes()


    # Draw the 3D green cube **after** the point cloud
    gl.glColor3f(0.0, 1.0, 0.0)  # Ensure the cube is green
    gl.glPushMatrix()


    gl.glTranslatef(0, 2, 0)    # Custom translation
    gl.glRotatef(50, -1, 0, 0)  # Custom rotation on x-axis


    draw_green_cube()
    gl.glPopMatrix()


    # Restore matrices for HUD
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.glOrtho(0, width, 0, height, -1, 1)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glLoadIdentity()
    gl.glDisable(gl.GL_DEPTH_TEST)








def run(dt):
    global w, h, tracks, tracker  # Ensure tracker is accessible and global
    window.set_caption("RealSense (%dx%d) %dFPS (%.2fms) %s" %
                       (w, h, 0 if dt == 0 else 1.0 / dt, dt * 1000,
                        "PAUSED" if state.paused else ""))


    if state.paused:
        return


    success, frames = pipeline.try_wait_for_frames(timeout_ms=0)
    if not success:
        return


    depth_frame = frames.get_depth_frame().as_video_frame()
    other_frame = frames.first(other_stream).as_video_frame()


    depth_frame = decimate.process(depth_frame)


    if state.postprocessing:
        for f in filters:
            depth_frame = f.process(depth_frame)


    # Grab new intrinsics (may be changed by decimation)
    depth_intrinsics = rs.video_stream_profile(
        depth_frame.profile).get_intrinsics()
    w, h = depth_intrinsics.width, depth_intrinsics.height


    color_image = np.asanyarray(other_frame.get_data())


    # Detect movement using background subtraction
    fg_mask, movement_boxes = detect_movement(color_image)


    # Run YOLO pose detection
    pose_results = pose_model(color_image, verbose=False)
    keypoints_data, detections = process_pose_results(pose_results)


    # Map track IDs to detection indices
    person_id_to_index = {}
    person_boxes = []
    for track in tracks:
        if not track.is_confirmed():
            continue
        track_id = track.track_id
        ltrb = track.to_ltrb()
        x1, y1, x2, y2 = map(int, ltrb)


        # Match track to detection
        for idx, det in enumerate(detections):
            det_box = det[0]
            det_ltrb = [det_box[0], det_box[1], det_box[0] + det_box[2], det_box[1] + det_box[3]]
            if bbox_iou(det_ltrb, ltrb) > 0.5:
                person_id_to_index[track_id] = idx
                break


        person_boxes.append({'track_id': track_id, 'bbox': (x1, y1, x2, y2)})


   
    # Compute movement status for each person
    person_moving_status = {}
    for person in person_boxes:
        track_id = person['track_id']
        x1, y1, x2, y2 = person['bbox']
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(color_image.shape[1], x2)
        y2 = min(color_image.shape[0], y2)
        person_fg_mask = fg_mask[y1:y2, x1:x2]
        movement_pixels = cv2.countNonZero(person_fg_mask)
        bbox_area = (x2 - x1) * (y2 - y1)
        movement_ratio = movement_pixels / bbox_area if bbox_area > 0 else 0
        person_moving_status[track_id] = movement_ratio > 0.01


    non_person_movement_boxes = get_non_person_movement_boxes(
        movement_boxes, person_boxes, movement_person_overlap_threshold=0.1
    )
    # Manually draw the keypoints and skeleton
    draw_keypoints_manually(color_image, keypoints_data)
    draw_skeleton(color_image, keypoints_data)


        # Map keypoints onto the point cloud
    # rotation_angles = [math.radians(control_panel.rotation_sliders[i].value()) for i in range(3)]
    # translation_values = [control_panel.translation_sliders[i].value() / 1000.0 for i in range(3)]
    # rotation_matrix_control = get_rotation_matrix(rotation_angles)


    # # Combine rotations and translations
    # total_rotation = np.dot(state.rotation, rotation_matrix_control)
    # total_translation = state.translation + translation_values


    # Build a list of (track_id, person_data)
    persons_with_ids = []
    for track_id, idx in person_id_to_index.items():
        if idx < len(keypoints_data):
            person_data = keypoints_data[idx]
            persons_with_ids.append((track_id, person_data))


    # Update tracker
    tracker, tracks = update_tracker(tracker, detections, color_image)


    colorized_depth = colorizer.colorize(depth_frame)
    depth_colormap = np.asanyarray(colorized_depth.get_data())


    if state.color:
        mapped_frame, color_source = other_frame, color_image
    else:
        mapped_frame, color_source = colorized_depth, depth_colormap


    points = pc.calculate(depth_frame)
    pc.map_to(mapped_frame)


    # Handle color source or size change
    fmt = convert_fmt(mapped_frame.profile.format())
    global image_data


    if (image_data.format, image_data.pitch) != (fmt, color_source.strides[0]):
        if state.color:
            global color_w, color_h
            image_w, image_h = color_w, color_h
        else:
            image_w, image_h = w, h


        empty = (gl.GLubyte * (image_w * image_h * 3))()
        image_data = pyglet.image.ImageData(image_w, image_h, fmt, empty)


    # Copy image data to pyglet
    image_data.set_data(fmt, color_source.strides[0], color_source.ctypes.data)


    verts = np.asarray(points.get_vertices(2)).reshape(h, w, 3)
    texcoords = np.asarray(points.get_texture_coordinates(2))


    if len(vertex_list.vertices) != verts.size:
        vertex_list.resize(verts.size // 3)
        # Need to reassign after resizing
        vertex_list.vertices = verts.ravel()
        vertex_list.tex_coords = texcoords.ravel()


    # Copy our data to pre-allocated buffers, this is faster than assigning...
    # pyglet will take care of uploading to GPU
    def copy(dst, src):
        """copy numpy array to pyglet array"""
        # timeit was mostly inconclusive, favoring slice assignment for safety
        np.array(dst, copy=False)[:] = src.ravel()
        # ctypes.memmove(dst, src.ctypes.data, src.nbytes)


    copy(vertex_list.vertices, verts)
    copy(vertex_list.tex_coords, texcoords)


    if state.lighting:
        # Compute normals
        dy, dx = np.gradient(verts, axis=(0, 1))
        n = np.cross(dx, dy)


        # OpenGL can normalize normals if GL_NORMALIZE is enabled
        copy(vertex_list.normals, n)


    if keys[pyglet.window.key.E]:
        points.export_to_ply('./out.ply', mapped_frame)




pyglet.clock.schedule(run)


try:
    pyglet.app.run()
finally:
    pipeline.stop()
