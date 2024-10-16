import os
import socket
import threading
import time
import random
from PIL import Image, ImageOps
import pygame

# Global variables for screen, images, cooldown tracking, and blinking
screen = None
images = None
last_update_time = 0  # Track the last update time
current_filename = "bt_20_cso.png"  # Default filename to keep track of the current image
blinking = False  # Track whether we're in a blinking state

def load_and_compress_images(directory, width, height):
    """Load and compress all images to the fixed size."""
    compressed_images = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.png'):
                try:
                    image = Image.open(os.path.join(root, file))
                    resized_image = ImageOps.fit(image, (width, height))
                    compressed_images.append((resized_image, file))  # Store filename
                except Exception as e:
                    print(f"Error loading {file}: {e}")
    return compressed_images

def display_image_by_filename(screen, images, filename):
    """Display the image matching the given filename."""
    for image, img_filename in images:
        if filename in img_filename:
            mode = image.mode
            size = image.size
            data = image.tobytes()
            image_surface = pygame.image.fromstring(data, size, mode)

            screen.fill((0, 0, 0))  # Clear screen
            screen.blit(image_surface, (0, 0))  # Display at top-left corner
            pygame.display.flip()
            print(f"Displayed: {filename}")
            return

    print(f"Image {filename} not found.")

def update_display_image(filename):
    """Update the displayed image when a filename is received, with a cooldown and a special transition."""
    global last_update_time, current_filename, blinking

    # Get the current time
    current_time = time.time()

    # Cooldown period of 0.5 seconds (500 milliseconds)
    cooldown = 0.5
    # Idle period check: Has it been at least 2 seconds since the last update?
    idle_period = 2

    # Check if enough time has passed since the last update
    if current_time - last_update_time >= cooldown:
        # If it's been idle for 2 or more seconds, apply the transition effect (o -> s -> o)
        if current_time - last_update_time >= idle_period:
            # Temporary transition to 's' for half a second
            temp_filename = filename[:-5] + 'w' + filename[-4:]  # Change last 'o' to 'w'
            if images and screen:
                display_image_by_filename(screen, images, temp_filename)
                time.sleep(0.5)  # Show 's' for half a second

        # Revert to the original filename ending with 'o'
        current_filename = filename
        display_image_by_filename(screen, images, current_filename)  # Display the final image with 'o'
        last_update_time = current_time  # Update the last update time
        blinking = False  # Stop blinking if we receive an update
    else:
        print("Update skipped due to cooldown.")

def start_server():
    """Socket server to listen for filename updates in a separate thread."""
    host = 'localhost'
    port = 65432

    def listen_for_filenames():
        """Background thread to listen for filenames."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((host, port))
            server_socket.listen()
            print(f"Server listening on {host}:{port}")

            while True:
                conn, addr = server_socket.accept()
                with conn:
                    data = conn.recv(1024).decode()  # Receive the filename
                    if data:
                        print(f"Received filename: {data}")
                        update_display_image(data)

    # Start the background thread
    thread = threading.Thread(target=listen_for_filenames, daemon=True)
    thread.start()

def simulate_blinking():
    """Simulate blinking after 2-5 seconds of no updates."""
    global last_update_time, current_filename, blinking

    while True:
        # Wait for a random time between 2 and 5 seconds
        time.sleep(random.uniform(2, 5))

        # Check if the time since the last update exceeds the threshold
        if not blinking and time.time() - last_update_time > 2:  # If no updates for 2+ seconds
            blinking = True  # Start the blinking sequence

            # Start blinking sequence
            if images and screen:
                # Modify the third-to-last character of the filename to simulate blinking
                base_filename = current_filename[:-7]  # Remove the 'c' and 'o.png'
                third_last_char = current_filename[-7]  # This will be 'c' to change to 'f'

                # Create filenames for blinking by replacing the third-to-last character with 'f'
                blink_filename_f = f"{base_filename}f" + current_filename[-6:]  # Change 'c' to 'f'

                display_image_by_filename(screen, images, blink_filename_f.replace('o', 'h'))  # Half-open
                time.sleep(0.2)  # Pause for 200 ms
                display_image_by_filename(screen, images, blink_filename_f.replace('o', 'c'))  # Closed
                time.sleep(0.2)  # Pause for 200 ms
                display_image_by_filename(screen, images, blink_filename_f.replace('o', 'h'))  # Half-open
                time.sleep(0.2)  # Pause for 200 ms
                display_image_by_filename(screen, images, current_filename)  # Return to original

def main():
    global screen, images

    image_width = 1920
    image_height = 540

    pygame.init()
    screen = pygame.display.set_mode((image_width, image_height))

    images = load_and_compress_images('eyeballImages_738', image_width, image_height)
    if not images:
        print("No images found.")
        return

    print(f"Loaded {len(images)} images.")
    display_image_by_filename(screen, images, current_filename)  # Display default image

    # Start the server to listen for filename updates in the background
    start_server()

    # Start the blinking mechanism in a separate thread
    blink_thread = threading.Thread(target=simulate_blinking, daemon=True)
    blink_thread.start()

    # Event loop to keep the window open until the user closes it
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # If the window close button is pressed
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Press ESC to exit
                    running = False

    pygame.quit()

if __name__ == "__main__":
    main()
