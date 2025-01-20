import math
from OpenGL.GL import *
from OpenGL.GLU import *
from live_config import LiveConfig

def draw_vertical_dividers(height=2.0, depth=30.0, center_x=0):
    """Draw multiple vertical dividers with evenly spaced x-coordinates."""
    # Access the LiveConfig instance
    live_config = LiveConfig.get_instance()
    if not live_config.show_vertical_planes:
        return
    
    num_divisions = live_config.num_divisions  # Total number of divider planes
    camera_z = live_config.camera_z

    # Define the total angle span (-90° to +90°) and calculate even steps
    total_angle_span = live_config.x_divider_angle
  # We want to cover a full 180° field
    angles = [-total_angle_span/2 + i * (total_angle_span / num_divisions) for i in range(num_divisions + 1)]

    for i in range(len(angles) - 1):
        angle1, angle2 = math.radians(angles[i]), math.radians(angles[i + 1])
        
        # Calculate x-coordinates using tangent for wider angles
        x1_far = depth * math.tan(angle1)
        x2_far = depth * math.tan(angle2)
        
        glPushMatrix()
        glTranslatef(center_x, 0, camera_z)
        
        # Draw the first wireframe plane
        glColor3f(0.5, 0.5, 0.5)  # Light gray color for wireframes
        glBegin(GL_LINE_LOOP)
        glVertex3f(0.0, -height / 2, 0.0)
        glVertex3f(0.0, height / 2, 0.0)
        glVertex3f(x1_far, height / 2, -depth)
        glVertex3f(x1_far, -height / 2, -depth)
        glEnd()
        
        # Draw the second wireframe plane
        glBegin(GL_LINE_LOOP)
        glVertex3f(0.0, -height / 2, 0.0)
        glVertex3f(0.0, height / 2, 0.0)
        glVertex3f(x2_far, height / 2, -depth)
        glVertex3f(x2_far, -height / 2, -depth)
        glEnd()
    
        glPopMatrix()

def fill_divider(index_to_fill, height=2.0, depth=30.0, center_x=0):
    """Fill only the space between two adjacent dividers at index_to_fill with a 3D transparent green object."""
    # Access the LiveConfig instance
    live_config = LiveConfig.get_instance()
    x_divider_angle = live_config.x_divider_angle
    num_divisions = live_config.num_divisions  # Use the same `num_divisions` for consistency
    camera_z = live_config.camera_z
    # Define the angle span and calculate even angles as in `draw_vertical_dividers`
    total_angle_span = x_divider_angle
    angles = [-total_angle_span / 2 + i * (total_angle_span / num_divisions) for i in range(num_divisions + 1)]
    
    # Get the two angles that define the space we want to fill
    angle1 = math.radians(angles[index_to_fill])
    angle2 = math.radians(angles[index_to_fill + 1])

    glPushMatrix()
    
    # Enable blending and set transparent green color
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 1.0, 0.0, 0.1)  # Semi-transparent green

    # Disable depth writing for transparency
    glDepthMask(GL_FALSE)

    # Calculate x-coordinates at depth for the specified space
    x1_far = depth * math.tan(angle1) + center_x
    x2_far = depth * math.tan(angle2) + center_x

    # Draw trapezoidal prism for the specified space
    glBegin(GL_QUADS)

    # Front face (near the camera)
    glVertex3f(center_x, -height / 2, camera_z)
    glVertex3f(center_x, height / 2, camera_z)
    glVertex3f(x2_far, height / 2, camera_z - depth)
    glVertex3f(x1_far, -height / 2, camera_z - depth)

    # Back face
    glVertex3f(x1_far, -height / 2, camera_z - depth)
    glVertex3f(x1_far, height / 2, camera_z - depth)
    glVertex3f(x2_far, height / 2, camera_z - depth)
    glVertex3f(x2_far, -height / 2, camera_z - depth)

    # Left side (angle1)
    glVertex3f(center_x, -height / 2, camera_z)
    glVertex3f(center_x, height / 2, camera_z)
    glVertex3f(x1_far, height / 2, camera_z - depth)
    glVertex3f(x1_far, -height / 2, camera_z - depth)

    # Right side (angle2)
    glVertex3f(center_x, -height / 2, camera_z)
    glVertex3f(center_x, height / 2, camera_z)
    glVertex3f(x2_far, height / 2, camera_z - depth)
    glVertex3f(x2_far, -height / 2, camera_z - depth)

    # Top side (between angle1 and angle2)
    glVertex3f(center_x, height / 2, camera_z)
    glVertex3f(x1_far, height / 2, camera_z - depth)
    glVertex3f(x2_far, height / 2, camera_z - depth)
    glVertex3f(center_x, height / 2, camera_z)

    # Bottom side (between angle1 and angle2)
    glVertex3f(center_x, -height / 2, camera_z)
    glVertex3f(x1_far, -height / 2, camera_z - depth)
    glVertex3f(x2_far, -height / 2, camera_z - depth)
    glVertex3f(center_x, -height / 2, camera_z)

    glEnd()

    # Re-enable depth writing after drawing the transparent object
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)
    glPopMatrix()

def draw_horizontal_dividers(camera_y=0, depth=30.0, width=50.0, num_slices=80):
    # Access the LiveConfig instance
    live_config = LiveConfig.get_instance()

    # Get divider values from LiveConfig
    y_top_divider = live_config.y_top_divider
    y_bottom_divider = live_config.y_bottom_divider
    y_top_divider_angle = live_config.y_top_divider_angle
    y_bottom_divider_angle = live_config.y_bottom_divider_angle

    # Calculate the y positions for the planes based on divider values
    # dividers = [
    #     (camera_y + y_top_divider, y_top_divider_angle),  # Top divider with its angle
    #     (camera_y - y_bottom_divider, y_bottom_divider_angle),  # Bottom divider with its angle
    # ]
    dividers = []
    if live_config.show_top_plane:
        dividers.append((camera_y + y_top_divider, live_config.y_top_divider_angle))
    if live_config.show_bottom_plane:
        dividers.append((camera_y - live_config.y_bottom_divider, live_config.y_bottom_divider_angle))

    # Loop through each divider position and angle to draw the wireframe plane
    for y, angle in dividers:
        glPushMatrix()  # Save the current matrix
        glColor4f(0.5, 0.5, 0.5, 0.5)  # Light gray color with moderate transparency

        # Translate to the starting position of the plane
        glTranslatef(0, y, live_config.camera_z)

        # Apply rotation to tilt the plane
        glRotatef(angle, 1.0, 0.0, 0.0)  # Rotate around the x-axis for tilt

        # Draw the outer border of the plane
        glBegin(GL_LINE_LOOP)
        glVertex3f(-width / 2, 0.0, 0.0)  # Bottom-left corner
        glVertex3f(width / 2, 0.0, 0.0)   # Bottom-right corner
        glVertex3f(width / 2, 0.0, -depth)  # Top-right corner (extending into -z)
        glVertex3f(-width / 2, 0.0, -depth)  # Top-left corner (extending into -z)
        glEnd()

        # Draw the internal grid lines
        glBegin(GL_LINES)
        # Vertical lines (along depth)
        for i in range(num_slices + 1):
            x = -width / 2 + i * (width / num_slices)
            glVertex3f(x, 0.0, 0.0)  # Near edge
            glVertex3f(x, 0.0, -depth)  # Far edge

        glEnd()

        glPopMatrix()  # Restore the previous matrix

def draw_movement_points(transformed_head_points, active_movement_id, active_movement_type):
    for track_id, head_point in transformed_head_points.items():
        if head_point is None:
            continue  
        x_h, y_h, z_h = head_point
        if track_id == active_movement_id:
            glColor3f(1,0, 0)  
        else:
            glColor3f(1,0, 0) 

        # Draw the sphere for the head point
        glPushMatrix()
        glTranslatef(x_h, y_h, z_h)  # Move to the head point's location
        gluSphere(gluNewQuadric(), 0.07, 30, 30)  # Draw a sphere with radius 0.05
        glPopMatrix()
    