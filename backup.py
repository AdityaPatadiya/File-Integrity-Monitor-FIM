import os
from datetime import datetime
import shutil
import json
import main1

BACKUP_BASELINE_FILE = "E:/coding/PYTHON/FIM_Backup/baseline_for_backup.json"
backup_directory = "E:/coding/PYTHON/FIM_Backup/"
backup_dir = None
backup_entries = {}

def normalized_path(path):
    return os.path.normpath(path)

def create_backup(source_dir):
    global backup_dir
    if not os.path.exists(source_dir):
        print(f"Source directory {source_dir} does not exist.")
        return

    timestamp = datetime.now().strftime(r"%Y_%m_%d_%H_%M_%S")
    backup_dir = normalized_path(os.path.join(backup_directory, f"backup_{timestamp}"))
    os.makedirs(backup_dir, exist_ok=True)


    backup_baseline = {}

    try:
        for item in os.listdir(source_dir):
            item_path = os.path.join(source_dir, item)
            if item_path == backup_dir:
                continue
            
            dest_path = os.path.join(backup_dir, item)
            if os.path.isdir(item_path):
                shutil.copytree(item_path, dest_path)
                backup_baseline[dest_path] = {
                    "type": "folder",
                    "hash": main1.calculate_folder_hash(item_path),
                    "last_modified": main1.get_formatted_time(os.path.getmtime(item_path)),
                }
            else:
                shutil.copy2(item_path, dest_path)
                backup_baseline[dest_path] = {
                    "type": "file",
                    "hash": main1.calculate_hash(dest_path),
                    "size": os.path.getsize(dest_path),
                    "last_modified": main1.get_formatted_time(os.path.getmtime(item_path)),
                }

        backup_baseline = {normalized_path(k): v for k, v in backup_baseline.items()}
        
        with open(BACKUP_BASELINE_FILE, "w") as f:
            json.dump(backup_baseline, f, indent=4)

        print(f"Backup created successfully at {backup_dir} and baseline saved.")
    except Exception as e:
        print(f"An error occurred during backup: {e}")

def create_and_load_backup_hash():
    """Create and load the hash for the backup directory."""
    global backup_entries

    for root, dirs, files in os.walk(backup_dir):
        for folder in dirs:
            folder_path = os.path.join(root, folder)
            backup_entries[folder_path] = {
                "type": "folder",
                "hash": main1.calculate_folder_hash(folder_path),
                "last_modified": main1.get_formatted_time(os.path.getmtime(folder_path)),
            }

        for file in files:
            file_path = os.path.join(root, file)
            backup_entries[file_path] = {
                "type": "file",
                "hash": main1.calculate_hash(file_path),
                "size": os.path.getsize(file_path),
                "last_modified": main1.get_formatted_time(os.path.getmtime(folder_path)),
            }
    
    backup_entries = {normalized_path(k): v for k, v in backup_entries.items()}
    
    with open(BACKUP_BASELINE_FILE, "w") as f:
        json.dump(backup_entries, f, indent=4)
    
    return main1.load_baseline(BACKUP_BASELINE_FILE)

