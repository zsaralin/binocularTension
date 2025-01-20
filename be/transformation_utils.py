
import numpy as np 

def apply_dynamic_transformation(verts, rotation, translation):
    """
    Apply rotation and translation to the point cloud vertices based on the control panel values.
    
    :param verts: The point cloud vertices to transform (can be a single point or an array of points)
    :param rotation: A list [rotate_x, rotate_y, rotate_z] with the rotation values in degrees
    :param translation: A list [translate_x, translate_y, translate_z] with the translation values
    :return: Transformed vertices
    """
    # Ensure verts is a 2D array, even if it's a single point
    verts = np.atleast_2d(verts)

    # Convert rotation angles from degrees to radians
    theta_x = np.radians(rotation[0])  # Rotation angle in radians for X-axis
    theta_y = np.radians(rotation[1])  # Rotation angle in radians for Y-axis
    theta_z = np.radians(rotation[2])  # Rotation angle in radians for Z-axis

    # Rotation matrix for X-axis
    cos_x, sin_x = np.cos(theta_x), np.sin(theta_x)
    rotation_matrix_x = np.array([
        [1, 0, 0],
        [0, cos_x, -sin_x],
        [0, sin_x, cos_x]
    ], dtype=np.float32)

    # Rotation matrix for Y-axis
    cos_y, sin_y = np.cos(theta_y), np.sin(theta_y)
    rotation_matrix_y = np.array([
        [cos_y, 0, sin_y],
        [0, 1, 0],
        [-sin_y, 0, cos_y]
    ], dtype=np.float32)

    # Rotation matrix for Z-axis
    cos_z, sin_z = np.cos(theta_z), np.sin(theta_z)
    rotation_matrix_z = np.array([
        [cos_z, -sin_z, 0],
        [sin_z, cos_z, 0],
        [0, 0, 1]
    ], dtype=np.float32)

    # Combine the rotation matrices: R = Rz * Ry * Rx
    combined_rotation_matrix = rotation_matrix_z @ rotation_matrix_y @ rotation_matrix_x

    # Apply the rotation to the vertices
    rotated_verts = verts @ combined_rotation_matrix.T

    # Apply translation
    translation_vector = np.array(translation, dtype=np.float32)
    transformed_verts = rotated_verts + translation_vector
    
    return transformed_verts.squeeze()  # Return to original shape if a single point