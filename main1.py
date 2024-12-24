import os
import json
import time
import hashlib
import logging
import backup
from pathlib import Path

logging.basicConfig(
    filename="FIM_Logging.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

POLL_INTERVAL = 1
BASELINE_FILE = "baseline.json"

def get_formatted_time(timestamp):
    """Convert a timestamp to a readable format."""
    return time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

def tracking_directory(directory):
    global current_entries
    current_entries = {}
    for root, dirs, files in os.walk(directory):
        for folder in dirs:
            folder_path = os.path.join(root, folder)  # here root used to track of the current folder.
            current_entries[folder_path] = {
                "type": "folder",
                "hash": calculate_folder_hash(folder_path),
                "last_modified": get_formatted_time(os.path.getmtime(folder_path)),
            }

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
        return None
    return sha256.hexdigest()

def calculate_folder_hash(folder_path):
    sha256 = hashlib.sha256()
    folder = Path(folder_path)
    # print(f"folder: {folder}")
    entries = sorted(folder.iterdir(), key=lambda x: x.name)
    # print(f"entries: {entries}")
    for entry in entries:
        # print(f"entry: {entry}")
        sha256.update(entry.name.encode())  # Include the name of the file/folder
        # print(f"{entry}: {sha256.hexdigest()}")
        if entry.is_dir():
            subfolder_hash = calculate_folder_hash(entry)
            sha256.update(subfolder_hash.encode())  # Include subfolder's hash
    return sha256.hexdigest()

def load_baseline(baseline_file):
    """Load the baseline from file and ensure it has valid structure."""
    if os.path.exists(baseline_file):
        with open(baseline_file, "r") as f:
            baseline = json.load(f)
            for entry_path, entry_data in baseline.items():
                if not isinstance(entry_data, dict):  # if entry_data is not dictionary, then it will print the unknown type.
                    baseline[entry_path] = {"type": "unknown"}
                elif "type" not in entry_data:
                    baseline[entry_path]["type"] = "file"
            return baseline
    return {}

def save_baseline(baseline):
    """Save the updated baseline to file."""
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=4)

def monitor_changes(directory):
    """Monitor files and folders for integrity changes."""
    original_content_map = {}
    backup_content_map = {}
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
            updated_baseline = baseline.copy()
            tracking_directory(directory)

            for (current_path, current_metadata), (backup_path, backup_metadata) in zip(current_entries.items(), backup_baseline.items()):
                if current_metadata["type"] == "file" and backup_metadata["type"] == "file":
                    current_hash_value = current_metadata.get("hash")
                    backup_hash_value = backup_metadata.get("hash")
                    if current_hash_value is None or backup_hash_value is None:
                        logging.warning(f"No hash value for file: {current_path if current_hash_value is None else backup_path}")
                        continue
                    original_content_map[current_path] = current_hash_value
                    backup_content_map[backup_path] = backup_hash_value
                    print(f"original_content_map_1: {original_content_map}\n")
                    print(f"backup_content_map_1: {backup_content_map}\n")
                elif current_metadata["type"] == "folder" and backup_metadata["type"] == "folder":
                    current_hash_value = current_metadata.get("hash")
                    backup_hash_value = backup_metadata.get("hash")
                    if current_hash_value == None or backup_hash_value == None:
                        logging.warning(f"No hash value for folder: {current_path if current_hash_value == None else backup_path}")
                    original_content_map[current_path] = current_hash_value
                    backup_content_map[backup_path] = backup_hash_value
                    print(f"original_content_map_2: {original_content_map}\n")
                    print(f"backup_content_map_2: {backup_content_map}\n")
                
                else:
                    print("'type' is missing from baseilne file.")
                    continue

            print(f"original_content_map: {original_content_map}\n")
            print(f"backup_content_map: {backup_content_map}\n")

            current_keys = set(original_content_map.values())
            backup_keys = set(backup_baseline.values())

            added_key = current_keys - backup_keys
            common_keys = current_keys & backup_keys
            deleted_keys = set(map(os.path.abspath, backup_baseline.keys())) - set(map(os.path.abspath, current_entries.keys()))

            # for key in common_keys:
            #     current_entry = current_entries.get(key, {})
            #     backup_entry = backup_content_map.get(key, {})

            #     if not isinstance(current_entry, dict) or not isinstance(backup_entry, dict):
            #         logging.error(f"Invalid entry format for key: {key}")
            #         continue

            #     if "type" not in current_entry or "type" not in backup_entry:
            #         logging.error(f"Missing 'type' key for key: {key}")
            #         continue

            #     if current_entry["type"] == "file":
            #         if "hash" not in current_entry or "hash" not in backup_entry:
            #             logging.error(f"Missing 'hash' key for file: {key}")
            #             continue

            #         if current_entry["hash"] != backup_entry["hash"]:
            #             logging.warning(f"File midified: {key}")
            #     elif "last_modified" in current_entry and "last_modified" in backup_entry:
            #         if current_entry["last_modified"] != backup_entry["last_modified"]:
            #             logging.warning(f"Folder modified: {key}")

            # for key in added_key:
            #     entry = current_entries.get(key, {})
            #     if not isinstance(entry, dict) or "type" not in entry:
            #         logging.error(f"Invalid entry format for added key: {key}")
            #         continue

            #     if entry["type"] == "file":
            #         logging.info(f"New File is added: {key}")
            #     else:
            #         logging.info(f"New folder is added: {key}")

            # for key in deleted_keys:
            #     if not isinstance(entry, dict) or "type" not in entry:
            #         logging.error(f"Invalid or missing 'type' key for deleted key: {key}")
            #         continue

            #     if entry["type"] == "file":
            #         logging.warning(f"File deleted: {key}")
            #     else:
            #         logging.warning(f"folder deleted: {key}")

            # updated_baseline = current_entries.copy()
            # baseline = updated_baseline
            # backup_baseline = baseline.copy()

            try:
                save_baseline(baseline)  # it will update the baseline.
            except Exception as e:
                logging.error(f"Failed to save baseline securely: {e}")

            time.sleep(POLL_INTERVAL)
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
