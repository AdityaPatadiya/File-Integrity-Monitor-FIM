import os
import json
import time
import hashlib
import logging

logging.basicConfig(
    filename="FIM_Logging.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration
MONITOR_DIR = "./test"  # Path to your monitored folder
BASELINE_FILE = "baseline.json"  # File to store baseline data
POLL_INTERVAL = 1  # Time interval in seconds

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
                if not isinstance(entry_data, dict):
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

def monitor_changes():
    """Monitor files and folders for integrity changes."""
    baseline = load_baseline()  # Load the baseline at the start

    while True:
        updated_baseline = baseline.copy()  # Start with a copy of the current baseline

        # Track files and folders in the monitored directory
        current_entries = {}
        for root, dirs, files in os.walk(MONITOR_DIR):
            # Track folders
            for folder in dirs:
                folder_path = os.path.join(root, folder)
                current_entries[folder_path] = {
                    "type": "folder",
                    "last_modified": os.path.getmtime(folder_path),
                }

            # Track files
            for file in files:
                file_path = os.path.join(root, file)
                current_entries[file_path] = {
                    "type": "file",
                    "hash": calculate_hash(file_path),
                    "size": os.path.getsize(file_path),
                    "last_modified": os.path.getmtime(file_path),
                }

        # Check for new or modified entries
        for entry_path, current_data in current_entries.items():
            baseline_entry = baseline.get(entry_path)
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
        save_baseline(baseline)

        time.sleep(POLL_INTERVAL)  # Monitor at regular intervals

if __name__ == "__main__":
    # Ensure the monitored folder exists
    if not os.path.exists(MONITOR_DIR):
        print(f"Creating monitored directory: {MONITOR_DIR}")
        os.makedirs(MONITOR_DIR)

    print("Starting File Integrity Monitor...")
    try:
        monitor_changes()
    except KeyboardInterrupt:
        print("\nFile Integrity Monitor stopped.")
