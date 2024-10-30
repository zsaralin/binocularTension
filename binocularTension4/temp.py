import os
from PIL import Image

def compress_images(input_folder, output_folder, max_size=(100, 100), quality=1):
    """
    Compresses images in the input folder and saves them to the output folder.

    Parameters:
        input_folder (str): Path to the folder containing HD images.
        output_folder (str): Path to the folder to save compressed images.
        max_size (tuple): Maximum width and height of the compressed images.
        quality (int): Quality of the compressed image (lower = more compression).
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Loop through all files in the input folder
    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)

        # Check if file is an image
        if os.path.isfile(file_path) and filename.lower().endswith(('jpg', 'jpeg', 'png')):
            with Image.open(file_path) as img:
                # Resize image while maintaining aspect ratio
                img.thumbnail(max_size, Image.LANCZOS )

                # Define output path
                output_path = os.path.join(output_folder, filename)

                # Save image with specified quality
                img.save(output_path, optimize=True, quality=quality)
                print(f"Compressed and saved: {output_path}")

if __name__ == "__main__":
    # Define your folders here
    input_folder = "./eyeballImages/201"
    output_folder = "./eyeballImages/201_mini"
    
    # Compress images
    compress_images(input_folder, output_folder)
