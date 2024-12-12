import os
import shutil
from datetime import datetime

def create_backup(source_dir):
    backup_directory = "E:/FIM_Backup/"
    # Ensure the source directory exists
    if not os.path.exists(source_dir):
        print(f"Source directory {source_dir} does not exist.")
        return

    # Define the backup directory name
    timestamp = datetime.now().strftime(r"%Y_%m_%d_%H'%M'%S")
    backup_dir = os.path.join(backup_directory, f"backup_{timestamp}")

    # Create the backup directory
    os.makedirs(backup_dir, exist_ok=True)

    try:
        # Copy files and subdirectories to the backup directory
        for item in os.listdir(source_dir):
            item_path = os.path.join(source_dir, item)
            if item_path == backup_dir:
                continue  # Skip copying the backup directory into itself
            
            dest_path = os.path.join(backup_dir, item)
            if os.path.isdir(item_path):
                shutil.copytree(item_path, dest_path)
            else:
                shutil.copy2(item_path, dest_path)

        print(f"Backup created successfully at {backup_dir}")
    except Exception as e:
        print(f"An error occurred during backup: {e}")

# Example usage
source_directory = r"E:\coding\PYTHON\FIM\test"
create_backup(source_directory)
