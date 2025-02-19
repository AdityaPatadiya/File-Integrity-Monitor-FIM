import os
import json
import time
import hashlib
import logging

from pathlib import Path
from src.utils.database import database_operation
import config.logging_config as logging_config


class FIM_monitor:
    def __init__(self):
        self.BASELINE_FILE = r"data\baselines\baseline.json"
        self.POLL_INTERVAL = 3
        self.current_entries = {}
        self.baseline_fle_path = os.path.abspath(self.BASELINE_FILE)
        self.database_instance = database_operation()
        self.database_instance.database_table_creation()

    def get_formatted_time(self, timestamp):
        """Convert a timestamp to a readable format."""
        return time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

    def tracking_directory(self, directory):
        """Traking the monitored directories to create baseline.json file."""
        for root, dirs, files in os.walk(directory):
            for folder in dirs:
                folder_path = os.path.join(root, folder)  # here root used to track of the current folder.
                self.current_entries[folder_path] = {
                    "type": "folder",
                    "hash": self.calculate_folder_hash(folder_path),
                    "last_modified": self.get_formatted_time(os.path.getmtime(folder_path)),
                }

            for file in files:
                file_path = os.path.join(root, file)
                self.current_entries[file_path] = {
                    "type": "file",
                    "hash": self.calculate_hash(file_path),
                    "size": os.path.getsize(file_path),
                    "last_modified": self.get_formatted_time(os.path.getmtime(folder_path)),
                }
        return self.current_entries

    def calculate_hash(self, file_path):
        """Calculate the SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(4096):
                    sha256.update(chunk)
                sha256.update(os.path.basename(file_path).encode())
        except (IsADirectoryError, FileNotFoundError):
            return None
        return sha256.hexdigest()

    def calculate_folder_hash(self, folder_path):
        """Calculate the SHA-256 hash of a folder."""
        sha256 = hashlib.sha256()
        folder = Path(folder_path)
        sha256.update(folder.name.encode())
        entries = sorted(folder.iterdir(), key=lambda x: x.name)
        for entry in entries:
            sha256.update(entry.name.encode())  # Include the name of the file/folder
            if entry.is_dir():
                subfolder_hash = self.calculate_folder_hash(entry)
                sha256.update(subfolder_hash.encode())  # Include subfolder's hash
        return sha256.hexdigest()

    def save_baseline(self, baseline):
        """Save the updated baseline to file."""
        try:
            with open(self.BASELINE_FILE, "w") as f:
                json.dump(baseline, f, indent=4)
            self.database_instance.store_information(self.current_entries)
        except Exception as e:
            logging.error(f"Error saving baseline: {e}")

    def load_baseline(self, baseline_file):
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
