import os
from datetime import datetime
import shutil
import json
import main1

BACKUP_BASELINE_FILE = "../FIM_Backup/baseline_for_backup.json"
backup_directory = "../FIM_Backup/"

def create_backup(source_dir):
    global backup_dir
    # Ensure the source directory exists
    if not os.path.exists(source_dir):
        print(f"Source directory {source_dir} does not exist.")
        return

    # Define the backup directory name
    timestamp = datetime.now().strftime(r"%Y_%m_%d_%H'%M'%S")
    backup_dir = os.path.join(backup_directory, f"backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)


    backup_baseline = {}

    try:
        # Copy files and subdirectories to the backup directory
        for item in os.listdir(source_dir):
            item_path = os.path.join(source_dir, item)
            if item_path == backup_dir:
                continue  # Skip copying the backup directory into itself
            
            dest_path = os.path.join(backup_dir, item)
            if os.path.isdir(item_path):
                shutil.copytree(item_path, dest_path)
                # Add folder metadata to the backup baeline
                backup_baseline[dest_path] = {
                    "type": "folder",
                    "last_modified": main1.get_formatted_time(os.path.getmtime(item_path)),
                }
            else:
                shutil.copy2(item_path, dest_path)
                # Add file metadata to the backup baseline
                backup_baseline[dest_path] = {
                    "type": "file",
                    "hash": main1.calculate_hash(dest_path),
                    "size": os.path.getsize(dest_path),
                    "last_modified": main1.get_formatted_time(os.path.getmtime(item_path)),
                }
        with open(BACKUP_BASELINE_FILE, "w") as f:
            json.dump(backup_baseline, f, indent=4)

        print(f"Backup created successfully at {backup_dir} and baseline saved.")
    except Exception as e:
        print(f"An error occurred during backup: {e}")

def create_and_load_backup_hash():
    """Create and load the hash for the backup directory."""
    main1.tracking_directory(backup_dir)
    
    # Save the hashes to the backup baseline file
    with open(BACKUP_BASELINE_FILE, "w") as f:
        json.dump(main1.current_entries, f, indent=4)
    
    # Load the baseline for further use
    return main1.load_baseline(BACKUP_BASELINE_FILE)

