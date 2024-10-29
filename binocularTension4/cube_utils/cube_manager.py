import json
from OpenGL.GL import *
from OpenGL.GLU import *

class CubeManager:
    _instance = None  # Class-level attribute to store the singleton instance

    @classmethod
    def get_instance(cls, file_path='./cubes.json'):
        """Get the singleton instance of CubeManager."""
        if cls._instance is None:
            cls._instance = CubeManager(file_path)
        return cls._instance

    def __init__(self, file_path='./cubes.json'):
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

    def add_cube(self, cube_id, x, y, z, width, height):
        """Add a cube to the manager."""
        self.cubes[cube_id] = {
            "x": x,
            "y": y,
            "z": z,
            "width": width,
            "height": height
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
            draw_cube(x, y, z, width, height)


def draw_cube(x, y, z, width, height):
    """Draw a cube centered at (x, y, z) with specified width and height."""
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(0.0, 0.0, 1.0)  # Set color to blue

    glBegin(GL_QUADS)

    # Front face
    glVertex3f(-width / 2, -height / 2, width / 2)
    glVertex3f(width / 2, -height / 2, width / 2)
    glVertex3f(width / 2, height / 2, width / 2)
    glVertex3f(-width / 2, height / 2, width / 2)

    # Back face
    glVertex3f(-width / 2, -height / 2, -width / 2)
    glVertex3f(width / 2, -height / 2, -width / 2)
    glVertex3f(width / 2, height / 2, -width / 2)
    glVertex3f(-width / 2, height / 2, -width / 2)

    # Left face
    glVertex3f(-width / 2, -height / 2, -width / 2)
    glVertex3f(-width / 2, -height / 2, width / 2)
    glVertex3f(-width / 2, height / 2, width / 2)
    glVertex3f(-width / 2, height / 2, -width / 2)

    # Right face
    glVertex3f(width / 2, -height / 2, -width / 2)
    glVertex3f(width / 2, -height / 2, width / 2)
    glVertex3f(width / 2, height / 2, width / 2)
    glVertex3f(width / 2, height / 2, -width / 2)

    # Top face
    glVertex3f(-width / 2, height / 2, -width / 2)
    glVertex3f(width / 2, height / 2, -width / 2)
    glVertex3f(width / 2, height / 2, width / 2)
    glVertex3f(-width / 2, height / 2, width / 2)

    # Bottom face
    glVertex3f(-width / 2, -height / 2, -width / 2)
    glVertex3f(width / 2, -height / 2, -width / 2)
    glVertex3f(width / 2, -height / 2, width / 2)
    glVertex3f(-width / 2, -height / 2, width / 2)

    glEnd()
    glPopMatrix()
