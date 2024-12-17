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
