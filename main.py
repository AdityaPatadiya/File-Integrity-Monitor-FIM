import os
import json
import time
import hashlib
import logging
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
BASELINE_FILE = "baseline.json"  # File to store baseline data
POLL_INTERVAL = 1  # Time interval in seconds

def get_formatted_time(timestamp):
    """Convert a timestamp to a readable format."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

def calculate_name_hash(file_path):
    """Calculate the SHA-256 hash of a file name."""
    file_name = os.path.basename(file_path)
    return hashlib.sha256(file_name.encode()).hexdigest()

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

def load_baseline():
    """Load the baseline from file and ensure it has valid structure."""
    if os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE, "r") as f:
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
        baseline = load_baseline()
    except Exception as e:
        logging.error(f"Failed to load baseline: {e}")
        baseline = {}

    while True:
        renamed_files = {}
        updated_baseline = baseline.copy()  # Start with a copy of the current baseline
        deleted_files = set(baseline.keys())
        current_entries = {}
        # Track files and folders in the monitored directory
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
                    "name_hash": calculate_name_hash(file_path),
                    "content_hash": calculate_hash(file_path),
                    "size": os.path.getsize(file_path),
                    "last_modified": get_formatted_time(os.path.getmtime(folder_path)),
                }

        # Check for new or modified entries
        for entry_path, current_data in current_entries.items():
            baseline_entry = baseline.get(entry_path)  # take all the entry path from baseline.
            if not isinstance(baseline_entry, dict):
                # Potentially new entry; store for cross-checking
                renamed_files[entry_path] = current_data
            elif current_data["type"] == "file":
                # Check for name or content modification
                if current_data["content_hash"] == baseline_entry.get("content_hash"):
                    if current_data["name_hash"] != baseline_entry.get("name_hash"):
                        logging.info(f"File renamed: {entry_path}")
                if current_data["content_hash"] != baseline_entry.get("content_hash"):
                    logging.error(f"File content modified: {entry_path}")
                updated_baseline[entry_path] = current_data
                deleted_files.discard(entry_path)
            elif current_data["last_modified"] != baseline_entry.get("last_modified"):
                # Modified folder
                logging.warning(f"Folder modified: {entry_path}")
                updated_baseline[entry_path] = current_data
                deleted_files.discard(entry_path)

        # Track for renamed and deleted files and folder
        for entry_path in list(deleted_files):  # Iterate over remaining "deleted" entries
            baseline_entry = baseline[entry_path]
            if baseline_entry["type"] == "file":
                for potential_new_path, current_data in renamed_files.items():
                    # Match content hashes to identify renames
                    if current_data["content_hash"] == baseline_entry.get("content_hash"):
                        logging.info(f"File renamed from {entry_path} to {potential_new_path}")
                        updated_baseline[potential_new_path] = current_data
                        renamed_files.pop(potential_new_path)
                        deleted_files.discard(entry_path)  # Remove from deleted files
                        break
                else:
                    # If no match, it is genuinely deleted
                    logging.warning(f"{baseline_entry['type'].capitalize()} deleted: {entry_path}")
                    updated_baseline.pop(entry_path, None)
            else:
                logging.warning(f"Folder deleted: {entry_path}")
                updated_baseline.pop(entry_path, None)
        
        # Remaining renamed_files are genuienly new files.
        for entry_path, current_data in renamed_files.items():
            logging.info(f"New {current_data['type']} added: {entry_path}")
            updated_baseline[entry_path] = current_data

        # Update the baseline
        baseline = updated_baseline
        try:
            save_baseline(baseline)
            # save_baseline_with_signature(baseline)
        except Exception as e:
            logging.error(f"Failed to save baseline: {e}")

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
                "name_hash": calculate_name_hash(file_path),
                "content_hash": calculate_hash(file_path),
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
