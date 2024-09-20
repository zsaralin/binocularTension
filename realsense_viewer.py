import pyrealsense2 as rs
import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import mediapipe as mp

# Global variables to store the checkbox states and mouse position
show_rgb = True
show_depth = True
track_skeleton = True  # By default, tracking is enabled
mouse_coords = (0, 0)
depth_value_at_mouse = None

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Toggle function for checkboxes
def toggle_stream():
    global show_rgb, show_depth, track_skeleton
    show_rgb = rgb_var.get()
    show_depth = depth_var.get()
    track_skeleton = track_var.get()

# Create a pipeline
pipeline = rs.pipeline()

# Configure the pipeline to stream RGB and depth frames
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)  # Depth stream
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)  # RGB stream

# Start streaming
pipeline.start(config)

# Align the depth frame to the RGB frame
align_to = rs.stream.color
align = rs.align(align_to)

# Create the Tkinter window
root = tk.Tk()
root.title("RealSense Stream with Depth Range Filtering")

# Create the canvas to display the video streams and gradient line
canvas_width = 1280 + 260  # 1280 for RGB + Depth, 260 for white panel
canvas_height = 480
canvas = tk.Canvas(root, width=canvas_width, height=canvas_height)
canvas.pack()

# Create the checkbox for RGB stream
rgb_var = tk.BooleanVar(value=True)
rgb_check = tk.Checkbutton(root, text="Show RGB", variable=rgb_var, command=toggle_stream)
rgb_check.pack(side=tk.LEFT)

# Create the checkbox for Depth stream
depth_var = tk.BooleanVar(value=True)
depth_check = tk.Checkbutton(root, text="Show Depth", variable=depth_var, command=toggle_stream)
depth_check.pack(side=tk.LEFT)

# Create the checkbox for skeletal tracking
track_var = tk.BooleanVar(value=True)
track_check = tk.Checkbutton(root, text="Track Skeleton", variable=track_var, command=toggle_stream)
track_check.pack(side=tk.LEFT)

# Create sliders for minimum and maximum depth
min_depth_label = tk.Label(root, text="Min Depth (m):")
min_depth_label.pack(side=tk.LEFT)
min_depth_slider = tk.Scale(root, from_=0.0, to=10.0, resolution=0.1, orient=tk.HORIZONTAL)
min_depth_slider.set(0.5)  # Set default min depth
min_depth_slider.pack(side=tk.LEFT)

max_depth_label = tk.Label(root, text="Max Depth (m):")
max_depth_label.pack(side=tk.LEFT)
max_depth_slider = tk.Scale(root, from_=0.0, to=10.0, resolution=0.1, orient=tk.HORIZONTAL)
max_depth_slider.set(3.0)  # Set default max depth
max_depth_slider.pack(side=tk.LEFT)

# Mouse callback function to get x, y position and depth value
def mouse_callback(event):
    global mouse_coords, depth_value_at_mouse
    x, y = event.x, event.y
    mouse_coords = (x, y)
    # Check if the mouse is over the combined image area
    combined_width = 0
    if show_rgb and show_depth:
        combined_width = 640 * 2  # 640 width for RGB and depth each
    elif show_rgb or show_depth:
        combined_width = 640
    else:
        combined_width = 0  # No image displayed

    if 0 <= x < combined_width and 0 <= y < 480:
        # Determine if mouse is over depth image
        if show_rgb and show_depth:
            # Depth image is on the right half
            if x >= 640:
                depth_x = x - 640
                depth_y = y
                # Get depth value from depth frame
                if depth_x < depth_frame.get_width() and depth_y < depth_frame.get_height():
                    depth_value_at_mouse = depth_frame.get_distance(int(depth_x), int(depth_y))
                else:
                    depth_value_at_mouse = None
            else:
                depth_value_at_mouse = None
        elif show_depth:
            # Depth image occupies the entire combined image
            depth_x = x
            depth_y = y
            if depth_x < depth_frame.get_width() and depth_y < depth_frame.get_height():
                depth_value_at_mouse = depth_frame.get_distance(int(depth_x), int(depth_y))
            else:
                depth_value_at_mouse = None
        else:
            depth_value_at_mouse = None
    else:
        depth_value_at_mouse = None

# Function to calculate the midpoint between two landmarks
def calculate_midpoint(landmark1, landmark2, width, height):
    x1, y1 = int(landmark1.x * width), int(landmark1.y * height)
    x2, y2 = int(landmark2.x * width), int(landmark2.y * height)
    midpoint = ((x1 + x2) // 2, (y1 + y2) // 2)
    return midpoint

# Function to draw a full-height gradient line
def draw_full_height_gradient_line(midpoint, canvas_size=(260, 200), line_thickness=10):
    # Create a white rectangle background
    white_panel = np.ones((canvas_size[1], canvas_size[0], 3), dtype=np.uint8) * 255

    # Define colors for the gradient line
    white = (255, 255, 255)
    black = (0, 0, 0)

    # Calculate line start and end points (full height)
    start_point = (midpoint[0], 0)
    end_point = (midpoint[0], canvas_size[1])

    # Draw the main black line in the center
    cv2.line(white_panel, start_point, end_point, black, thickness=line_thickness)

    # Create gradient lines fading to white on both sides
    gradient_thickness = line_thickness * 3  # Extend the gradient more
    for i in range(gradient_thickness):
        alpha = i / float(gradient_thickness)
        color = [int(black[j] * (1 - alpha) + white[j] * alpha) for j in range(3)]

        # Draw the fading lines to the left and right of the black line
        cv2.line(white_panel, (start_point[0] - line_thickness // 2 - i, start_point[1]),
                 (end_point[0] - line_thickness // 2 - i, end_point[1]),
                 color, thickness=1)

        cv2.line(white_panel, (start_point[0] + line_thickness // 2 + i, start_point[1]),
                 (end_point[0] + line_thickness // 2 + i, end_point[1]),
                 color, thickness=1)

    return white_panel

# Function to update the canvas with the current video frames and gradient lines
def update_canvas():
    global depth_frame
    # Wait for a coherent pair of frames: depth and RGB
    frames = pipeline.wait_for_frames()

    # Align depth frame to RGB frame
    aligned_frames = align.process(frames)

    # Get aligned depth and RGB frames
    depth_frame = aligned_frames.get_depth_frame()
    rgb_frame = aligned_frames.get_color_frame()

    if not depth_frame or not rgb_frame:
        root.after(10, update_canvas)
        return

    # Convert images to numpy arrays
    depth_image = np.asanyarray(depth_frame.get_data())
    rgb_image = np.asanyarray(rgb_frame.get_data())

    # Apply color map to depth frame for better visualization
    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

    # Ensure both depth and RGB images have the same size
    depth_colormap_resized = cv2.resize(depth_colormap, (rgb_image.shape[1], rgb_image.shape[0]))

    # Create a white panel for gradient lines (260x200)
    white_panel = np.ones((200, 260, 3), dtype=np.uint8) * 255

    # Get min and max depth from sliders
    min_depth = min_depth_slider.get()
    max_depth = max_depth_slider.get()

    # Apply skeletal tracking if enabled
    if track_skeleton:
        # Process the RGB image with MediaPipe Pose
        results = pose.process(cv2.cvtColor(rgb_image, cv2.COLOR_BGR2RGB))

        if results.pose_landmarks:
            height, width, _ = rgb_image.shape
            # Draw skeleton on RGB image
            mp.solutions.drawing_utils.draw_landmarks(
                rgb_image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
            )
            # Draw skeleton on depth image
            mp.solutions.drawing_utils.draw_landmarks(
                depth_colormap_resized, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)
            )

            # Calculate midpoint between shoulders
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            midpoint = calculate_midpoint(left_shoulder, right_shoulder, width, height)

            # Get depth at the midpoint
            if 0 <= midpoint[0] < depth_frame.get_width() and 0 <= midpoint[1] < depth_frame.get_height():
                person_depth = depth_frame.get_distance(int(midpoint[0]), int(midpoint[1]))

                # Check if the person's depth is within the specified range
                if min_depth <= person_depth <= max_depth:
                    # Scale midpoint to white panel size
                    scaled_midpoint = (int(midpoint[0] * 260 / width), int(midpoint[1] * 200 / height))
                    # Draw the gradient line on the white panel
                    white_panel = draw_full_height_gradient_line(scaled_midpoint, canvas_size=(260, 200))
                else:
                    # Do not draw the gradient line if depth is out of range
                    pass
            else:
                # Midpoint is out of depth frame bounds
                pass

    # Combine the images based on the checkbox state
    if show_rgb and show_depth:
        combined_image = np.hstack((rgb_image, depth_colormap_resized))
    elif show_rgb:
        combined_image = rgb_image
    elif show_depth:
        combined_image = depth_colormap_resized
    else:
        combined_image = np.zeros_like(rgb_image)

    # Display the depth value and coordinates if the mouse is hovering
    if depth_value_at_mouse is not None:
        x, y = mouse_coords
        cv2.putText(combined_image, f"X: {x}, Y: {y}, Depth: {depth_value_at_mouse:.2f}m",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    # Convert images to PIL format
    combined_image_rgb = cv2.cvtColor(combined_image, cv2.COLOR_BGR2RGB)
    img_combined = Image.fromarray(combined_image_rgb)
    imgtk_combined = ImageTk.PhotoImage(image=img_combined)

    white_panel_rgb = cv2.cvtColor(white_panel, cv2.COLOR_BGR2RGB)
    img_white_panel = Image.fromarray(white_panel_rgb)
    imgtk_white_panel = ImageTk.PhotoImage(image=img_white_panel)

    # Update the canvas with the new images
    canvas.create_image(0, 0, anchor=tk.NW, image=imgtk_combined)
    canvas.create_image(1280, 0, anchor=tk.NW, image=imgtk_white_panel)

    # Keep references to avoid garbage collection
    canvas.image_combined = imgtk_combined
    canvas.image_white_panel = imgtk_white_panel

    # Schedule the next update
    root.after(10, update_canvas)

# Bind mouse motion event to the canvas
canvas.bind('<Motion>', mouse_callback)

# Start the first canvas update
update_canvas()

# Run the Tkinter main loop
root.mainloop()

# Stop the pipeline when the window is closed
pipeline.stop()
