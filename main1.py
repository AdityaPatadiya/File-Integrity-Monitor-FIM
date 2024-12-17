import os
import json
import time
import stat
import shutil
import hashlib
import logging
from datetime import datetime
# from encryption_for_baseline_file.baseline_security import (
#     save_baseline_encrypted, load_baseline_encrypted, generate_key
# )
# from encryption_for_baseline_file.digital_signature import (
#     save_baseline_with_signature, load_baseline_with_signature, generate_key_pair
# )

logging.basicConfig(
    filename="FIM_Logging.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration
POLL_INTERVAL = 1  # Time interval in seconds
BASELINE_FILE = "baseline.json"  # File to store baseline data
BACKUP_BASELINE_FILE = "../FIM_Backup/baseline_for_backup.json"
backup_directory = "../FIM_Backup/"

def get_formatted_time(timestamp):
    """Convert a timestamp to a readable format."""
    return time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

def create_backup(source_dir):
    global backup_dir
    # Ensure the source directory exists
    if not os.path.exists(source_dir):
        print(f"Source directory {source_dir} does not exist.")
        return

    # Define the backup directory name
    timestamp = datetime.now().strftime(r"%Y_%m_%d_%H'%M'%S")
    backup_dir = os.path.join(backup_directory, f"backup_{timestamp}")

    # Create the backup directory
    os.makedirs(backup_dir, exist_ok=True)
    os.chmod(backup_dir, 0o700)
    print(os.R_OK)
    print(os.W_OK)
    print(os.X_OK)

    try:
        # Copy files and subdirectories to the backup directory
        for item in os.listdir(source_dir):
            item_path = os.path.join(source_dir, item)
            if item_path == backup_dir:
                continue  # Skip copying the backup directory into itself
            
            dest_path = os.path.join(backup_dir, item)
            if os.path.isdir(item_path):
                shutil.copytree(item_path, dest_path)
                print(f"Copied directory {item_path} to {dest_path}")
            else:
                shutil.copy2(item_path, dest_path)
                print(f"Copied file {item_path} to {dest_path}")

        print(f"Backup created successfully at {backup_dir}")
    except Exception as e:
        print(f"An error occurred during backup: {e}")

def create_and_load_backup_hash():
    """create and load the hash for backup directory."""
    print("'create_and_load_backup_hash' function called")
    calculate_hash(backup_dir)
    load_baseline(BACKUP_BASELINE_FILE)

def calculate_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):
                sha256.update(chunk)
    except (IsADirectoryError, FileNotFoundError):
        return None  # Directories or missing files don't have hashes
    return sha256.hexdigest()

def load_baseline(baseline_file):
    """Load the baseline from file and ensure it has valid structure."""
    if os.path.exists(baseline_file):
        with open(baseline_file, "r") as f:
            baseline = json.load(f)
            # Add missing "type" keys for older baselines
            for entry_path, entry_data in baseline.items():
                if not isinstance(entry_data, dict):  # if entry_data is not dictionary, then it will print the unknown type.
                    # Handle invalid or missing entries
                    baseline[entry_path] = {"type": "unknown"}
                elif "type" not in entry_data:
                    # Default type to "file" for compatibility
                    baseline[entry_path]["type"] = "file"
            return baseline
    return {}

def save_baseline(baseline):
    """Save the updated baseline to file."""
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=4)

def monitor_changes(directory):
    """Monitor files and folders for integrity changes."""
    try:
        create_backup(directory)
        create_and_load_backup_hash()
        baseline = load_baseline(BASELINE_FILE)
    except Exception as e:
        logging.error(f"Failed to load baseline: {e}")
        baseline = {}

    while True:
        updated_baseline = baseline.copy()  # Start with a copy of the current baseline

        # Track files and folders in the monitored directory
        current_entries = {}
        for root, dirs, files in os.walk(directory):  # go through all folders(dirs) and files(files) in the folders.
            # Track folders
            for folder in dirs:
                folder_path = os.path.join(root, folder)  # here root used to track of the current folder.
                current_entries[folder_path] = {
                    "type": "folder",
                    "last_modified": get_formatted_time(os.path.getmtime(folder_path)),
                }

            # Track files
            for file in files:
                file_path = os.path.join(root, file)
                current_entries[file_path] = {
                    "type": "file",
                    "hash": calculate_hash(file_path),
                    "size": os.path.getsize(file_path),
                    "last_modified": get_formatted_time(os.path.getmtime(folder_path)),
                }

        # Check for new or modified entries
        for entry_path, current_data in current_entries.items():
            baseline_entry = baseline.get(entry_path)  # take all the entry path from baseline.
            if not isinstance(baseline_entry, dict):
                # New entry
                logging.info(f"New {current_data['type']} added: {entry_path}")
                updated_baseline[entry_path] = current_data
            elif current_data["type"] == "file" and current_data["hash"] != baseline_entry.get("hash"):
                # Modified file
                logging.error(f"File modified: {entry_path}")
                updated_baseline[entry_path] = current_data
            elif current_data["last_modified"] != baseline_entry.get("last_modified"):
                # Modified folder
                logging.warning(f"Folder modified: {entry_path}")
                updated_baseline[entry_path] = current_data

        # Check for deleted entries
        for entry_path in baseline:
            if entry_path not in current_entries:
                entry_type = baseline[entry_path]["type"]
                logging.warning(f"{entry_type.capitalize()} deleted: {entry_path}")
                updated_baseline.pop(entry_path, None)

        # Update the baseline
        baseline = updated_baseline
        try:
            save_baseline(baseline)
            # save_baseline_with_signature(baseline)
        except Exception as e:
            logging.error(f"Failed to save baseline securely: {e}")

        time.sleep(POLL_INTERVAL)  # Monitor at regular intervals

def view_baseline():
    """View the current baseline data."""
    if os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE, "r") as f:
            print(json.dumps(json.load(f), indent=4))
    else:
        print("Baseline file not found.")

def reset_baseline(directory):
    """Reset the baseline file."""
    print("Resetting baseline...")
    if os.path.exists(BASELINE_FILE):
        os.remove(BASELINE_FILE)
    # Generate a fresh baseline
    baseline = {}
    for root, dirs, files in os.walk(directory):
        for folder in dirs:
            folder_path = os.path.join(root, folder)
            baseline[folder_path] = {
                "type": "folder",
                "last_modified": get_formatted_time(os.path.getmtime(folder_path)),
            }
        for file in files:
            file_path = os.path.join(root, file)
            baseline[file_path] = {
                "type": "file",
                "hash": calculate_hash(file_path),
                "size": os.path.getsize(file_path),
                "last_modified": get_formatted_time(os.path.getmtime(folder_path)),
            }
    save_baseline(baseline)
    print("Baseline reset complete.")

def view_logs():
    """View the logs from the logging file."""
    if os.path.exists("FIM_Logging.log"):
        with open("FIM_Logging.log", "r") as log_file:
            print(log_file.read())
    else:
        print("Log file not found.")
