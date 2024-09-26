import socket
import pygame
from PIL import Image, ImageOps
import os
import select  # For non-blocking socket I/O

# Flag to indicate if an image is currently being displayed
is_displaying = False
image_dict = {}

def load_and_compress_images(directory, screen_width, screen_height):
    total_files = 0
    for root, _, files in os.walk(directory):
        total_files += len([file for file in files if file.endswith('.png')])

    print(f"Found {total_files} PNG images in {directory}.")

    loaded_files = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.png') and 'bt_' in file:  # Only consider PNG images with 'bt_' prefix
                image_path = os.path.join(root, file)
                try:
                    # Extract the image number from the filename, e.g., bt_0_cso.png -> 0
                    image_index = int(file.split('_')[1])

                    # Load the image at full resolution
                    print(f"Loading image: {image_path}")
                    image = Image.open(image_path)

                    # Resize the image to fit the screen size while keeping the aspect ratio
                    resized_image = ImageOps.contain(image, (screen_width, screen_height))

                    # Store the image in a dictionary with its index
                    image_dict[image_index] = resized_image

                    loaded_files += 1
                    print(f"Compressed and loaded image {loaded_files}/{total_files} (index: {image_index})")
                except Exception as e:
                    print(f"Error loading {image_path}: {e}")

    print(f"Finished loading {loaded_files}/{total_files} images.")

def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 65432))  # Blocking connect call
    print("Connected to point cloud server.")
    client_socket.setblocking(False)  # Set the socket to non-blocking mode
    return client_socket

def map_x_to_image_index(x, frame_width):
    """
    Map the X-coordinate to an image index from 0 (left) to 41 (right),
    with 20 representing the center.
    """
    if x < 0:
        x = 0
    elif x > frame_width:
        x = frame_width

    normalized_x = x / frame_width  # Get a value between 0 and 1
    image_index = int(normalized_x * 41)  # Map it to a value between 0 and 41
    return image_index

def receive_blob_coords(client_socket, screen, frame_width, frame_height):
    global is_displaying
    try:
        # Check if there's data to read using select
        ready_to_read, _, _ = select.select([client_socket], [], [], 0)
        if ready_to_read and not is_displaying:  # Only proceed if we're not currently displaying an image
            data = client_socket.recv(1024)
            if data:
                coords = data.decode().strip().split(",")
                blob_coords = tuple(map(float, coords))  # (x, y, z)

                # Map the x-coordinate to the corresponding image index
                image_index = map_x_to_image_index(blob_coords[0], frame_width)

                if image_index in image_dict:
                    is_displaying = True  # Set flag to prevent more updates during display
                    display_image(screen, image_dict[image_index], blob_coords)
                    is_displaying = False  # Reset flag after display is complete
    except Exception as e:
        print(f"Error receiving coordinates: {e}")

def display_image(screen, image, blob_coords=None):
    mode = image.mode
    size = image.size
    data = image.tobytes()

    try:
        if mode == 'RGBA':
            image_surface = pygame.image.fromstring(data, size, 'RGBA')
        else:
            image_surface = pygame.image.fromstring(data, size, 'RGB')

        screen.fill((0, 0, 0))  # Clear the screen before displaying new image
        screen.blit(image_surface, ((screen.get_width() - image_surface.get_width()) // 2,
                                    (screen.get_height() - image_surface.get_height()) // 2))

        # Display the blob coordinates on the screen, if available
        if blob_coords:
            font = pygame.font.Font(None, 36)
            coords_text = f"Blob Coordinates: X={blob_coords[0]:.2f}, Y={blob_coords[1]:.2f}, Z={blob_coords[2]:.2f}"
            text = font.render(coords_text, True, (255, 255, 255))
            screen.blit(text, (50, 50))  # Display the text at (50, 50)

        pygame.display.flip()
    except Exception as e:
        print(f"Error displaying image: {e}")

def run_display_images():
    client_socket = connect_to_server()  # Connect to the point cloud backend

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    directory = 'images'
    screen_width, screen_height = pygame.display.get_surface().get_size()

    # Load the images before starting the display loop
    print("Loading images, please wait...")
    load_and_compress_images(directory, screen_width, screen_height)
    print("Images loaded.")

    # Main event loop
    running = True
    while running:
        receive_blob_coords(client_socket, screen, screen_width, screen_height)  # Check for incoming blob coordinates

        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.QUIT:
                running = False

        pygame.display.update()

    pygame.quit()
    client_socket.close()

if __name__ == "__main__":
    run_display_images()
