import os
import shutil

# Set the parent directory path
parent_dir = os.path.abspath('./fe/eyeballImages')
subfolders = ['blue', 'brown']

def remove_folders(folder_path):
    """Removes all subfolders that start with 'f' within the given folder."""
    print(f"Removing 'f' subfolders in: {folder_path}")

    for root, dirs, _ in os.walk(folder_path, topdown=False):
        for dir_name in dirs:
            if dir_name.lower().startswith('f'):
                dir_path = os.path.join(root, dir_name)
                print(f"Deleting folder: {dir_path}")
                shutil.rmtree(dir_path)

def flatten_files(folder_path):
    """Moves all files from subdirectories to the parent folder and removes empty subdirectories."""
    print(f"Flattening files in: {folder_path}")

    for root, dirs, files in os.walk(folder_path, topdown=False):
        # Move files to the parent directory
        for file in files:
            file_path = os.path.join(root, file)
            destination_path = os.path.join(folder_path, file)

            # Rename if a file with the same name already exists
            if os.path.exists(destination_path):
                base, extension = os.path.splitext(file)
                counter = 1
                while os.path.exists(destination_path):
                    destination_path = os.path.join(folder_path, f"{base}_{counter}{extension}")
                    counter += 1

            print(f"Moving file: {file_path} -> {destination_path}")
            shutil.move(file_path, destination_path)

        # Remove now-empty folders
        if os.path.isdir(root) and root != folder_path and not os.listdir(root):
            print(f"Removing empty folder: {root}")
            os.rmdir(root)

# Run for both 'blue' and 'brown' folders
for subfolder in subfolders:
    folder_path = os.path.join(parent_dir, subfolder)
    if os.path.exists(folder_path):
        remove_folders(folder_path)  # First pass: Remove 'f' subfolders
        flatten_files(folder_path)   # Second pass: Flatten files and clean empty folders


