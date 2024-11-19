import os
import shutil

# Set the parent directory path
parent_dir = './eyeballImages/Gab'

def empty_subfolders():
    # Walk through the directory
    for root, dirs, files in os.walk(parent_dir, topdown=False):
        for file in files:
            # Define the source and destination paths
            file_path = os.path.join(root, file)
            destination_path = os.path.join(parent_dir, file)
            
            # If the file already exists in the destination, rename it
            if os.path.exists(destination_path):
                # Rename the file by appending a number if it already exists
                base, extension = os.path.splitext(file)
                counter = 1
                while os.path.exists(destination_path):
                    destination_path = os.path.join(parent_dir, f"{base}_{counter}{extension}")
                    counter += 1

            # Move the file to the parent directory
            shutil.move(file_path, destination_path)
        
        # Remove empty folders
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):  # Check if the folder is empty
                os.rmdir(dir_path)
empty_subfolders()

# def count_fsc_files(parent_dir):
#     count = 0
#     # Walk through the directory and subdirectories
#     for root, dirs, files in os.walk(parent_dir):
#         for file in files:
#             # Check if the file ends with 'fsc'
#             if file.endswith("fsc.jpg"):
#                 count += 1
#     return count

# fsc_file_count = count_fsc_files(parent_dir)
# print(f"Number of files ending with 'fsc.jpg': {fsc_file_count}")