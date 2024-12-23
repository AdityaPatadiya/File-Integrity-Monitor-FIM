import os
import json
import time
import hashlib
import logging
import backup

logging.basicConfig(
    filename="FIM_Logging.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration
POLL_INTERVAL = 1  # Time interval in seconds
BASELINE_FILE = "baseline.json"  # File to store baseline data

def get_formatted_time(timestamp):
    """Convert a timestamp to a readable format."""
    return time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

def tracking_directory(directory):
    global current_entries
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
        backup.create_backup(directory)
        backup.create_and_load_backup_hash()
        backup_baseline = backup.backup_entries
        # for key in list(backup_baseline.keys()):
        #     normalized_key = os.path.abspath(key)
        #     if normalized_key != key:
        #         backup_baseline[normalized_key] = backup_baseline.pop(key)
        baseline = load_baseline(BASELINE_FILE)
    except Exception as e:
        logging.error(f"Failed to load baseline: {e}")
        baseline = {}

    while True:
        try:
            updated_baseline = baseline.copy()  # Start with a copy of the current baseline
            # Track files and folders in the monitored directory
            tracking_directory(directory)
            
            current_keys = set(current_entries.keys())
            backup_keys = set(backup_baseline.keys())

            added_key = current_keys - backup_keys
            common_keys = current_keys & backup_keys
            deleted_keys = set(map(os.path.abspath, backup_baseline.keys())) - set(map(os.path.abspath, current_entries.keys()))

            for key in common_keys:
                current_entry = current_entries.get(key, {})
                backup_entry = backup_baseline.get(key, {})

                if not isinstance(current_entry, dict) or not isinstance(backup_entry, dict):
                    logging.error(f"Invalid entry format for key: {key}")
                    continue

                if "type" not in current_entry or "type" not in backup_entry:
                    logging.error(f"Missing 'type' key for key: {key}")
                    continue

                if current_entry["type"] == "file":
                    if "hash" not in current_entry or "hash" not in backup_entry:
                        logging.error(f"Missing 'hash' key for file: {key}")
                        continue

                    if current_entry["hash"] != backup_entry["hash"]:
                        logging.warning(f"File midified: {key}")
                elif "last_modified" in current_entry and "last_modified" in backup_entry:
                    if current_entry["last_modified"] != backup_entry["last_modified"]:
                        logging.warning(f"Folder modified: {key}")

            for key in added_key:
                entry = current_entries.get(key, {})
                if not isinstance(entry, dict) or "type" not in entry:
                    logging.error(f"Invalid entry format for added key: {key}")
                    continue

                if entry["type"] == "file":
                    logging.info(f"New File is added: {key}")
                else:
                    logging.info(f"New folder is added: {key}")

            for key in deleted_keys:
                if not isinstance(entry, dict) or "type" not in entry:
                    logging.error(f"Invalid or missing 'type' key for deleted key: {key}")
                    continue

                if entry["type"] == "file":
                    logging.warning(f"File deleted: {key}")
                else:
                    logging.warning(f"folder deleted: {key}")

            # Update the baseline
            updated_baseline = current_entries.copy()
            baseline = updated_baseline
            backup_baseline = baseline.copy()

            try:
                save_baseline(baseline)
                # save_baseline_with_signature(baseline)
            except Exception as e:
                logging.error(f"Failed to save baseline securely: {e}")

            time.sleep(POLL_INTERVAL)  # Monitor at regular intervals
        except Exception as e:
            print(f"Error while monitoring: {e}")

def view_baseline():
    """View the current baseline data."""
    if os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE, "r") as f:
            print(json.dumps(json.load(f), indent=4))
    else:
        print("Baseline file not found.")

def reset_baseline(directory):
    """Reset the baseline file."""
    print("Resetting baseline and backup_baseline...")
    if os.path.exists(BASELINE_FILE) and os.path.exists(backup.BACKUP_BASELINE_FILE):
        os.remove(BASELINE_FILE)
        os.remove(backup.BACKUP_BASELINE_FILE)

    backup.create_backup(directory)
    if not backup.backup_dir:
        print("Backup directory not initialized. Aborting reset.")
        return

    tracking_directory(directory)
    save_baseline(current_entries)
    tracking_directory(backup.backup_dir)
    backup.create_and_load_backup_hash()
    print("Baseline and backup_baseline reset complete.")

def view_logs():
    """View the logs from the logging file."""
    if os.path.exists("FIM_Logging.log"):
        with open("FIM_Logging.log", "r") as log_file:
            print(log_file.read())
    else:
        print("Log file not found.")
