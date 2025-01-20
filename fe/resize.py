import os
from PIL import Image

def compress_images(input_folder, output_folder, max_size=(300, 300), quality=30):
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

def resize_images_in_folder(input_folder, output_folder, target_size=(1280, 400)): #1920, 540
    """
    Resizes all JPEG images in the input_folder to the target_size and saves them in the output_folder.
    
    :param input_folder: Path to the folder containing the original images.
    :param output_folder: Path to the folder where resized images will be saved.
    :param target_size: A tuple (width, height) representing the target resolution.
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Supported image extensions
    image_extensions = ('.jpg', '.jpeg', '.JPG', '.JPEG')

    # Iterate over all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(image_extensions):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            try:
                with Image.open(input_path) as img:
                    # Skip resizing if the image already has the target size
                    if img.size == target_size:
                        print(f"Skipping {filename}: already at target size {target_size}")
                        continue
                    
                    # Resize the image to the target size
                    resized_img = img.resize(target_size, Image.LANCZOS)
                    # Save the resized image to the output folder
                    resized_img.save(output_path, quality=95)
                    print(f"Resized and saved: {output_path}")
            except Exception as e:
                print(f"Error processing {input_path}: {e}")

if __name__ == "__main__":
    input_folder = './eyeballImages/V1'     # Replace with your input folder path
    output_folder = './eyeballImages/V1_smalld'   # Replace with your output folder path

    resize_images_in_folder(input_folder, output_folder,  target_size=(1280, 400))

    output_folder = './eyeballImages/V1_'   # Replace with your output folder path

    resize_images_in_folder(input_folder, output_folder,  target_size=(1920, 540))

    output_folder = './eyeballImages/V1_mini'   # Replace with your output folder path

    compress_images(input_folder, output_folder)