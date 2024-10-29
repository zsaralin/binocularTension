import numpy as np
import math

# Rotation matrix function
def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis, dtype=np.float32)
    axis = axis / np.linalg.norm(axis)
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    return np.array([
        [a*a + b*b - c*c - d*d, 2*(b*c - a*d),     2*(b*d + a*c)],
        [2*(b*c + a*d),     a*a + c*c - b*b - d*d, 2*(c*d - a*b)],
        [2*(b*d - a*c),     2*(c*d + a*b),     a*a + d*d - b*b - c*c]
    ])

def get_rotation_matrix(angles):
    Rx = np.array([[1, 0, 0],
                   [0, math.cos(angles[0]), -math.sin(angles[0])],
                   [0, math.sin(angles[0]), math.cos(angles[0])]])
    Ry = np.array([[math.cos(angles[1]), 0, math.sin(angles[1])],
                   [0, 1, 0],
                   [-math.sin(angles[1]), 0, math.cos(angles[1])]])
    Rz = np.array([[math.cos(angles[2]), -math.sin(angles[2]), 0],
                   [math.sin(angles[2]), math.cos(angles[2]), 0],
                   [0, 0, 1]])
    return Rz @ Ry @ Rx

def apply_transform(verts, rotation_matrix, translation_values):
    return (rotation_matrix @ verts.T).T + np.array(translation_values)

def convert_depth_pixel_to_metric_coordinate(depth, pixel_x, pixel_y, intrinsics):
    x = (pixel_x - intrinsics.ppx) / intrinsics.fx * depth
    y = (pixel_y - intrinsics.ppy) / intrinsics.fy * depth
    z = depth
    return x, y, z
