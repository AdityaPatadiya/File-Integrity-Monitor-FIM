import os
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any
from typing import Optional

from src.utils.database import database_operation
import config.logging_config as logging_config


class FIM_monitor:
    def __init__(self):
        self.database_instance = database_operation()
        self.database_instance._initialize_schema()
        self.current_entries: Dict[str, Dict[str, Any]] = {}

    def get_formatted_time(self, timestamp: float) -> str:
        """Convert a timestamp to a readable format."""
        return time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

    def tracking_directory(self, directory: str) -> Dict[str, Dict[str, Any]]:
        """
        Track the monitored directory and store baseline in the database.
        Returns a dictionary of file/folder metadata.
        """
        print("tracking_direcoties method called.\n")
        self.current_entries = {}

        for root, dirs, files in os.walk(directory):
            for folder in dirs:
                folder_path = os.path.join(root, folder)
                try:
                    folder_hash = self.calculate_folder_hash(folder_path)
                    last_modified = self.get_formatted_time(os.path.getmtime(folder_path))
                except Exception as e:
                    print(f"Error processing folder: {e}")

                self.current_entries[folder_path] = {
                    "type": "folder",
                    "hash": folder_hash,
                    "last_modified": last_modified,
                }

                # Store in database
                self.database_instance.record_file_event(
                    directory_path=directory,
                    file_path=folder_path,
                    file_hash=folder_hash,
                    last_modified=last_modified,
                    status='current'
                )

            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_hash = self.calculate_hash(file_path)
                    last_modified = self.get_formatted_time(os.path.getmtime(file_path))
                except Exception as e:
                    print(f"Error processing file: {e}")

                self.current_entries[file_path] = {
                    "type": "file",
                    "hash": file_hash,
                    "size": os.path.getsize(file_path),
                    "last_modified": last_modified,
                }

                # Store in database
                self.database_instance.record_file_event(
                    directory_path=directory,
                    file_path=file_path,
                    file_hash=file_hash,
                    last_modified=last_modified,
                    status='current'
                )

        return self.current_entries

    def calculate_hash(self, file_path: str) -> Optional[str]:
        """Calculate the SHA-256 hash of a file."""
        print("File hash calculated.\n")
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(4096):
                    sha256.update(chunk)
                sha256.update(os.path.basename(file_path).encode())
            return sha256.hexdigest()
        except (IsADirectoryError, FileNotFoundError, PermissionError) as e:
            logging.error(f"Error calculating hash for {file_path}: {str(e)}")
            return None

    def calculate_folder_hash(self, folder_path: str) -> str:
        """Calculate the SHA-256 hash of a folder."""
        print("Folder hash calculated.\n")
        sha256 = hashlib.sha256()
        folder = Path(folder_path)
        sha256.update(folder.name.encode())

        # Sort entries for consistent hashing
        entries = sorted(folder.iterdir(), key=lambda x: x.name)
        for entry in entries:
            sha256.update(entry.name.encode())
            if entry.is_dir():
                subfolder_hash = self.calculate_folder_hash(entry)
                sha256.update(subfolder_hash.encode())
            elif entry.is_file():
                file_hash = self.calculate_hash(entry)
                if file_hash:
                    sha256.update(file_hash.encode())
        
        return sha256.hexdigest()
