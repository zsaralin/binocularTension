import os
import numpy as np
from PIL import Image

def add_noise(image, noise_level=10):
    """Add random noise to an image to increase the perceived detail."""
    # Convert the image to a numpy array
    img_array = np.array(image)

    # Generate random noise (values between -noise_level and +noise_level)
    noise = np.random.randint(-noise_level, noise_level, img_array.shape, dtype='int16')

    # Add noise and clip the values to be within valid pixel range (0-255)
    noisy_img = img_array.astype('int16') + noise
    noisy_img = np.clip(noisy_img, 0, 255)  # Ensure pixel values are valid

    # Convert back to uint8 for display/saving
    noisy_img = noisy_img.astype('uint8')

    return Image.fromarray(noisy_img)

def add_perlin_noise(image, scale=100):
    """Add Perlin-like noise to the image to simulate more detail."""
    img_array = np.array(image)
    h, w, c = img_array.shape
    noise = np.random.normal(loc=0, scale=scale, size=(h, w, c))

    # Add Perlin noise and clip the values to be in the valid range
    noisy_img = img_array.astype('float') + noise
    noisy_img = np.clip(noisy_img, 0, 255)

    noisy_img = noisy_img.astype('uint8')

    return Image.fromarray(noisy_img)

def add_detail_to_image(input_image_path, output_image_path, noise_level=10, noise_type='random'):
    """Add detail (noise) to an image and save it with increased complexity."""
    # Open the image
    image = Image.open(input_image_path)

    # Add noise to the image based on the selected type
    if noise_type == 'random':
        noisy_image = add_noise(image, noise_level=noise_level)
    elif noise_type == 'perlin':
        noisy_image = add_perlin_noise(image, scale=noise_level)
    else:
        raise ValueError("Unsupported noise type. Choose 'random' or 'perlin'.")

    # Save the noisy image
    noisy_image.save(output_image_path)
    print(f"Saved noisy image to: {output_image_path}")

def process_images_in_folder(input_folder, noise_level=10, noise_type='random'):
    """Process all images in the input folder and save them to a new folder with noise added."""
    # Create the output folder by appending '_noise' to the original folder name
    output_folder = input_folder.rstrip("/") + "_noise"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Loop through all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".jpg") or filename.endswith(".png"):  # Only process image files
            input_image_path = os.path.join(input_folder, filename)
            output_image_path = os.path.join(output_folder, filename)  # Save with the same filename in the new folder

            # Add noise and save the image to the output folder
            add_detail_to_image(input_image_path, output_image_path, noise_level=noise_level, noise_type=noise_type)

# Example usage:
input_folder = "./eyeballImages_738"  # Replace with your input folder path
noise_level = 100  # Adjust the noise level as needed
noise_type = "random"  # Choose either 'random' or 'perlin'

# Process all images in the folder and add noise
process_images_in_folder(input_folder, noise_level, noise_type)
