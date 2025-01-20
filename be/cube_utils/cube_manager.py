import json
from OpenGL.GL import *
from OpenGL.GLU import *

class CubeManager:
    _instance = None  # Class-level attribute to store the singleton instance

    @classmethod
    def get_instance(cls, file_path='./cube_utils/cubes.json'):
        """Get the singleton instance of CubeManager."""
        if cls._instance is None:
            cls._instance = CubeManager(file_path)
        return cls._instance

    def __init__(self, file_path='./cube_utils/cubes.json'):
        if CubeManager._instance is not None:
            raise Exception("This class is a singleton! Use `get_instance()` to access it.")
        self.file_path = file_path
        self.cubes = {}
        self.load_cubes()

    def load_cubes(self):
        """Load cubes from the JSON file."""
        try:
            with open(self.file_path, 'r') as f:
                self.cubes = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.cubes = {}  # If the file doesn't exist or is invalid, start with an empty dictionary

    def save_cubes(self):
        """Save cubes to the JSON file."""
        with open(self.file_path, 'w') as f:
            json.dump(self.cubes, f, indent=4)

    def add_cube(self, cube_id, x, y, z, width, height, depth, rotation_x=0, rotation_y=0, rotation_z=0):
        """Add a cube with position, size, and rotation to the manager."""
        self.cubes[cube_id] = {
            "x": x,
            "y": y,
            "z": z,
            "width": width,
            "height": height,
            "depth": depth,
            "rotation_x": rotation_x,
            "rotation_y": rotation_y,
            "rotation_z": rotation_z
        }

    def remove_cube(self, cube_id):
        """Remove a cube from the manager."""
        if cube_id in self.cubes:
            del self.cubes[cube_id]

    def draw_cubes(self):
        """Draw all cubes currently in the manager."""
        for cube_id, cube_data in self.cubes.items():
            x = cube_data['x']
            y = cube_data['y']
            z = cube_data['z']
            width = cube_data['width']
            height = cube_data['height']
            depth = cube_data['depth']
            rotation_x = cube_data['rotation_x']
            rotation_y = cube_data['rotation_y']
            rotation_z = cube_data['rotation_z']
            draw_cube(x, y, z, width, height, depth, rotation_x, rotation_y, rotation_z)

    def is_point_in_cubes(self, point):
        """Check if a point is within any cube in the manager."""
        px, py, pz = point
        for cube_id, cube in self.cubes.items():
            cx, cy, cz = cube['x'], cube['y'], cube['z']
            half_width = cube['width'] / 2
            half_height = cube['height'] / 2
            half_depth = cube['depth'] / 2

            # Check if point is within the bounds for each dimension
            in_x = cx - half_width <= px <= cx + half_width
            in_y = cy - half_height <= py <= cy + half_height
            in_z = cz - half_depth <= pz <= cz + half_depth

            if in_x and in_y and in_z:
                return True
        return False

def draw_cube(x, y, z, width, height, depth, rotation_x=0, rotation_y=0, rotation_z=0):
    """Draw a cube centered at (x, y, z) with specified width, height, depth, and rotation angles."""
    glPushMatrix()
    glTranslatef(x, y, z)
    
    # Apply rotations around each axis
    glRotatef(rotation_x, 1, 0, 0)  # Rotate around X axis
    glRotatef(rotation_y, 0, 1, 0)  # Rotate around Y axis
    glRotatef(rotation_z, 0, 0, 1)  # Rotate around Z axis
    
    # Set color to semi-transparent blue and enable blending for transparency
    glColor4f(0.0, 0.0, 1.0, 0.5)  # Semi-transparent blue
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Draw each face of the cube as a filled quad for transparency
    glBegin(GL_QUADS)
    
    # Front face
    glVertex3f(-width / 2, -height / 2, depth / 2)
    glVertex3f(width / 2, -height / 2, depth / 2)
    glVertex3f(width / 2, height / 2, depth / 2)
    glVertex3f(-width / 2, height / 2, depth / 2)
    
    # Back face
    glVertex3f(-width / 2, -height / 2, -depth / 2)
    glVertex3f(width / 2, -height / 2, -depth / 2)
    glVertex3f(width / 2, height / 2, -depth / 2)
    glVertex3f(-width / 2, height / 2, -depth / 2)
    
    # Left face
    glVertex3f(-width / 2, -height / 2, -depth / 2)
    glVertex3f(-width / 2, -height / 2, depth / 2)
    glVertex3f(-width / 2, height / 2, depth / 2)
    glVertex3f(-width / 2, height / 2, -depth / 2)
    
    # Right face
    glVertex3f(width / 2, -height / 2, -depth / 2)
    glVertex3f(width / 2, -height / 2, depth / 2)
    glVertex3f(width / 2, height / 2, depth / 2)
    glVertex3f(width / 2, height / 2, -depth / 2)
    
    # Top face
    glVertex3f(-width / 2, height / 2, -depth / 2)
    glVertex3f(width / 2, height / 2, -depth / 2)
    glVertex3f(width / 2, height / 2, depth / 2)
    glVertex3f(-width / 2, height / 2, depth / 2)
    
    # Bottom face
    glVertex3f(-width / 2, -height / 2, -depth / 2)
    glVertex3f(width / 2, -height / 2, -depth / 2)
    glVertex3f(width / 2, -height / 2, depth / 2)
    glVertex3f(-width / 2, -height / 2, depth / 2)
    
    glEnd()

    # Draw wireframe outline
    glColor4f(0.0, 0.0, 1.0, 1.0)  # Solid blue for edges
    glBegin(GL_LINE_LOOP)

    # Front face outline
    glVertex3f(-width / 2, -height / 2, depth / 2)
    glVertex3f(width / 2, -height / 2, depth / 2)
    glVertex3f(width / 2, height / 2, depth / 2)
    glVertex3f(-width / 2, height / 2, depth / 2)

    # Back face outline
    glVertex3f(-width / 2, -height / 2, -depth / 2)
    glVertex3f(width / 2, -height / 2, -depth / 2)
    glVertex3f(width / 2, height / 2, -depth / 2)
    glVertex3f(-width / 2, height / 2, -depth / 2)

    # Left face outline
    glVertex3f(-width / 2, -height / 2, -depth / 2)
    glVertex3f(-width / 2, -height / 2, depth / 2)
    glVertex3f(-width / 2, height / 2, depth / 2)
    glVertex3f(-width / 2, height / 2, -depth / 2)

    # Right face outline
    glVertex3f(width / 2, -height / 2, -depth / 2)
    glVertex3f(width / 2, -height / 2, depth / 2)
    glVertex3f(width / 2, height / 2, depth / 2)
    glVertex3f(width / 2, height / 2, -depth / 2)

    # Top face outline
    glVertex3f(-width / 2, height / 2, -depth / 2)
    glVertex3f(width / 2, height / 2, -depth / 2)
    glVertex3f(width / 2, height / 2, depth / 2)
    glVertex3f(-width / 2, height / 2, depth / 2)

    # Bottom face outline
    glVertex3f(-width / 2, -height / 2, -depth / 2)
    glVertex3f(width / 2, -height / 2, -depth / 2)
    glVertex3f(width / 2, -height / 2, depth / 2)
    glVertex3f(-width / 2, -height / 2, depth / 2)

    glEnd()

    # Disable blending and restore settings
    glDisable(GL_BLEND)
    glPopMatrix()
