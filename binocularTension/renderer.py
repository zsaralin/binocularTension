import numpy as np
import cv2
import time
import pyrealsense2 as rs

class Renderer:
    def render_frame(self, verts, texcoords, color_source, depth_intrinsics, transform_gui, state):
        """Render the transformed point cloud in 3D and its 2D projection side by side."""
        now = time.time()

        # Create an output canvas large enough to display both 2D and 3D views side by side
        out_3d = np.zeros((480, 640, 3), dtype=np.uint8)  # For 3D rendering
        out_2d = np.zeros((480, 640, 3), dtype=np.uint8)  # For 2D projection

        # Render the 3D point cloud
        self.render_3d(out_3d, verts, texcoords, color_source, depth_intrinsics, transform_gui, state)

        # Render the 2D front view of the point cloud
        self.render_2d(out_2d, verts, transform_gui, state)

        # Combine the two views side by side
        combined_view = np.hstack((out_3d, out_2d))

        # Calculate frame timing
        dt = time.time() - now
        fps = 1.0 / dt if dt > 0 else 0  # Handle the case where dt is zero

        cv2.setWindowTitle(
            state.WIN_NAME,
            f"3D and 2D Views {combined_view.shape[1]}x{combined_view.shape[0]} @ {fps:.2f}FPS ({dt * 1000:.2f}ms)"
        )

        # Show the combined view
        cv2.imshow(state.WIN_NAME, combined_view)

    def render_3d(self, out, verts, texcoords, color_source, depth_intrinsics, transform_gui, state):
        """Render the 3D view of the point cloud."""
        out.fill(0)

        # Get Y-axis translation from the GUI
        _, y_translation, _ = transform_gui.get_translation()

        # Render grid with adjusted Y-axis position
        grid(out, (0, 0.5 + y_translation / 100.0, 1), size=1, n=10, state=state)

        # Render the camera frustum
        frustum(out, depth_intrinsics, state=state)

        # Render axes
        axes(out, view([0, 0, 0], state), state.rotation, size=0.1, thickness=1)

        # Render point cloud
        h, w = depth_intrinsics.height, depth_intrinsics.width
        if not state.scale or out.shape[:2] == (h, w):
            pointcloud(out, verts, texcoords, color_source, painter=True, state=state)  # Pass painter argument
        else:
            tmp = np.zeros((h, w, 3), dtype=np.uint8)
            pointcloud(tmp, verts, texcoords, color_source, painter=True, state=state)  # Pass painter argument
            tmp = cv2.resize(tmp, out.shape[:2][::-1], interpolation=cv2.INTER_NEAREST)
            np.putmask(out, tmp > 0, tmp)

    def render_2d(self, out, verts, transform_gui, state, fixed_scale=300.0):
        """Render the 2D representation of the 3D point cloud (front view) with smoothing."""
        out.fill(0)

        # Project to 2D and scale
        verts_2d = verts[:, :2]  # Keep only x and y coordinates
        verts_2d *= fixed_scale

        center_x = out.shape[1] // 2
        center_y = out.shape[0] // 2
        verts_2d[:, 0] += center_x
        verts_2d[:, 1] += center_y

        # Create a mask for valid points
        valid_points = (verts_2d[:, 0] >= 0) & (verts_2d[:, 0] < out.shape[1]) & \
                       (verts_2d[:, 1] >= 0) & (verts_2d[:, 1] < out.shape[0])

        # Get valid coordinates
        valid_x = verts_2d[valid_points][:, 0].astype(int)
        valid_y = verts_2d[valid_points][:, 1].astype(int)

        # Create a heatmap
        heatmap = np.zeros(out.shape[:2], dtype=np.float32)
        for x, y in zip(valid_x, valid_y):
            cv2.circle(heatmap, (x, y), 3, 1, -1)

        # Apply Gaussian blur to the heatmap
        heatmap = cv2.GaussianBlur(heatmap, (11, 11), 0)

        # Normalize the heatmap
        heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Threshold the heatmap to create a binary mask
        _, binary_mask = cv2.threshold(heatmap, 50, 255, cv2.THRESH_BINARY)

        # Apply morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
        binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by area
        min_area_threshold = 100
        large_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area_threshold]

        # Draw filled contours
        cv2.drawContours(out, large_contours, -1, (255, 255, 255), -1)

        # Apply edge smoothing
        out = cv2.GaussianBlur(out, (5, 5), 0)

        return out

    def draw_marker(self, out, position, color=(255, 255, 255), size=5, label=None):
        """Draw a small marker (point) at a specific 3D position, with optional label."""
        screen_pos = project_to_screen(position, out.shape)
        cv2.circle(out, screen_pos, size, color, -1)

        if label:
            cv2.putText(out, label, (screen_pos[0] + 10, screen_pos[1] + 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

def line3d(out, pt1, pt2, color=(0x80, 0x80, 0x80), thickness=1, state=None):
    """Draw a 3D line from pt1 to pt2."""
    p0 = project(pt1.reshape(-1, 3), out)[0]
    p1 = project(pt2.reshape(-1, 3), out)[0]
    if np.isnan(p0).any() or np.isnan(p1).any():
        return
    p0 = tuple(p0.astype(int))
    p1 = tuple(p1.astype(int))
    rect = (0, 0, out.shape[1], out.shape[0])
    inside, p0, p1 = cv2.clipLine(rect, p0, p1)
    if inside:
        cv2.line(out, p0, p1, color, thickness, cv2.LINE_AA)

def grid(out, pos, rotation=np.eye(3), size=1, n=10, color=(0x80, 0x80, 0x80), state=None):
    """Draw a grid on the XZ plane."""
    pos = np.array(pos)
    s = size / float(n)
    s2 = 0.5 * size
    for i in range(n + 1):
        x = -s2 + i * s
        line3d(out, view(pos + np.dot((x, 0, -s2), rotation), state),
               view(pos + np.dot((x, 0, s2), rotation), state), color)
    for i in range(n + 1):
        z = -s2 + i * s
        line3d(out, view(pos + np.dot((-s2, 0, z), rotation), state),
               view(pos + np.dot((s2, 0, z), rotation), state), color)

def axes(out, pos, rotation=np.eye(3), size=0.075, thickness=2, state=None):
    """Draw 3D axes."""
    line3d(out, pos, pos + np.dot((0, 0, size), rotation), (0xff, 0, 0), thickness)
    line3d(out, pos, pos + np.dot((0, size, 0), rotation), (0, 0xff, 0), thickness)
    line3d(out, pos, pos + np.dot((size, 0, 0), rotation), (0, 0, 0xff), thickness)

def frustum(out, intrinsics, state=None, color=(0x40, 0x40, 0x40)):
    """Draw camera's frustum."""
    orig = view([0, 0, 0], state)
    w, h = intrinsics.width, intrinsics.height

    for d in range(1, 6, 2):
        def get_point(x, y):
            p = rs.rs2_deproject_pixel_to_point(intrinsics, [x, y], d)
            line3d(out, orig, view(p, state), color)
            return p

        top_left = get_point(0, 0)
        top_right = get_point(w, 0)
        bottom_right = get_point(w, h)
        bottom_left = get_point(0, h)

        line3d(out, view(top_left, state), view(top_right, state), color)
        line3d(out, view(top_right, state), view(bottom_right, state), color)
        line3d(out, view(bottom_right, state), view(bottom_left, state), color)
        line3d(out, view(bottom_left, state), view(top_left, state), color)

def project(v, out):
    """Project 3D vector array to 2D."""
    h, w = out.shape[:2]  # Replace `out` with `state.out`
    view_aspect = float(h) / w

    # Ignore divide by zero for invalid depth
    with np.errstate(divide='ignore', invalid='ignore'):
        proj = v[:, :-1] / v[:, -1, np.newaxis] * (w * view_aspect, h) + (w / 2.0, h / 2.0)

    # Near clipping
    znear = 0.03
    proj[v[:, 2] < znear] = np.nan
    return proj

def view(v, state):
    """Apply view transformation on vector array."""
    return np.dot(v - state.pivot, state.rotation) + state.pivot - state.translation

def pointcloud(out, verts, texcoords, color, painter=True, state=None):
    """Draw point cloud with optional painter's algorithm."""
    if painter:
        v = view(verts, state)
        s = v[:, 2].argsort()[::-1]
        proj = project(v[s], out)  # Pass out to project
    else:
        proj = project(view(verts, state), out)  # Pass out to project

    if state.scale:
        proj *= 0.5 ** state.decimate

    h, w = out.shape[:2]
    j, i = proj.astype(np.uint32).T

    # Create a mask to ignore out-of-bound indices
    im = (i >= 0) & (i < h)
    jm = (j >= 0) & (j < w)
    m = im & jm

    cw, ch = color.shape[:2][::-1]
    if painter:
        v, u = (texcoords[s] * (cw, ch) + 0.5).astype(np.uint32).T
    else:
        v, u = (texcoords * (cw, ch) + 0.5).astype(np.uint32).T

    # Clip texcoords to image
    np.clip(u, 0, ch - 1, out=u)
    np.clip(v, 0, cw - 1, out=v)

    # Perform UV-mapping
    out[i[m], j[m]] = color[u[m], v[m]]

def project_to_screen(position, screen_shape):
    """Convert a 3D point to 2D screen coordinates."""
    x, y, z = position
    screen_x = int((x + 1) * screen_shape[1] // 2)  # Normalize x to screen width
    screen_y = int((1 - y) * screen_shape[0] // 2)  # Normalize y to screen height (invert for screen coordinates)

    return (screen_x, screen_y)
