import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# Global variables for z-axis rotation and zoom
z_rotation = 0
zoom_level = -10  # Starting zoom level (distance from the scene)
mouse_sensitivity = 0.2
zoom_speed = 0.5  # Speed at which the zoom changes
mouse_pressed = False  # To track if the mouse button is pressed
fov_angle = math.radians(115)  # Field of view in radians (45 degrees)

# Initialize the Pygame display and OpenGL
def init_display():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glEnable(GL_DEPTH_TEST)

# Draw a wireframe plane fanning out from the camera's perspective
def draw_fan_plane_wireframe(angle):
    plane_length = 10  # Length of the plane
    # Calculate the positions using trigonometry (based on the angle)
    x_start = math.sin(angle) * plane_length
    z_start = math.cos(angle) * plane_length

    glBegin(GL_LINE_LOOP)  # Use wireframe (GL_LINE_LOOP)
    # The planes should extend outward from the camera's perspective
    glVertex3f(0, 15, 0)   # Top center (origin point at camera)
    glVertex3f(0, -15, 0)  # Bottom center (origin point at camera)
    glVertex3f(x_start, -5, -z_start)  # Bottom outer point
    glVertex3f(x_start, 5, -z_start)   # Top outer point
    glEnd()

# Draw the 3D environment
def draw_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glPushMatrix()
    
    # Apply zoom (move the camera closer or farther away)
    glTranslatef(0, 0, zoom_level)

    # Apply z-axis rotation for horizontal view (rotate around the up axis)
    glRotatef(z_rotation, 0, 1, 0)
    
    # Calculate the spacing between planes to cover the entire FOV
    num_planes = 4  # Total number of planes
    fov_half_angle = fov_angle / 2
    angle_step = fov_angle / (num_planes - 1)  # Evenly divide the FOV

    # Draw fanning wireframe planes (angles spread evenly)
    for i in range(num_planes):
        angle = -fov_half_angle + i * angle_step  # Distribute planes within FOV
        glColor3f(0.5 + i * 0.1, 0.5, 0.5)  # Slightly different colors for each plane
        draw_fan_plane_wireframe(angle)
    
    glPopMatrix()

    pygame.display.flip()

# Draw a cube
def draw_cube():
    vertices = [
        [1, 1, -1], [1, -1, -1], [-1, -1, -1], [-1, 1, -1],
        [1, 1, 1], [1, -1, 1], [-1, -1, 1], [-1, 1, 1]
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7)
    ]

    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()

# Handle mouse movement for rotation
def handle_mouse_motion(mouse_dx):
    global z_rotation
    z_rotation += mouse_dx * mouse_sensitivity  # Only rotate around the z-axis (horizontal)

# Handle zoom (zoom in/out with mouse scroll or keys)
def handle_zoom(event):
    global zoom_level
    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 4:  # Mouse scroll up (zoom in)
            zoom_level += zoom_speed
        elif event.button == 5:  # Mouse scroll down (zoom out)
            zoom_level -= zoom_speed

def handle_keypress(event):
    global zoom_level
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP:  # Zoom in with the up arrow
            zoom_level += zoom_speed
        elif event.key == pygame.K_DOWN:  # Zoom out with the down arrow
            zoom_level -= zoom_speed

# Main loop
def main():
    global mouse_pressed
    init_display()
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == MOUSEMOTION and mouse_pressed:
                mouse_dx, _ = event.rel  # Only track horizontal (dx) movement
                handle_mouse_motion(mouse_dx)
            elif event.type == MOUSEBUTTONDOWN:
                handle_zoom(event)  # Handle zoom with mouse scroll
                if event.button == 1:  # Left mouse button pressed
                    mouse_pressed = True
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button released
                    mouse_pressed = False
            elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                handle_keypress(event)  # Handle zoom with keyboard up/down keys

        draw_scene()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
