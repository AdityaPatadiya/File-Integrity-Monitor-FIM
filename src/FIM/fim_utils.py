import os
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

from src.utils.database import database_operation
from config.logging_config import configure_logger


class FIM_monitor:
    def __init__(self):
        self.database_instance = database_operation()
        self.database_instance._initialize_schema()
        self.current_entries: Dict[str, Dict[str, Any]] = {}
        self.configure_logger = configure_logger()
        self.logger = None
        self.file_hash = None
        self.folder_hash = None
        self.last_modified = None

    def get_formatted_time(self, timestamp: float) -> str:
        """Convert a timestamp to a readable format."""
        return time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

    def tracking_directory(self, auth_user, directory: str) -> Dict[str, Dict[str, Any]]:
        """
        Track the monitored directory and store baseline in the database.
        Returns a dictionary of file/folder metadata.
        """
        self.current_entries = {}
        self.logger = self.configure_logger._get_or_create_logger(auth_user, directory)

        for root, dirs, files in os.walk(directory):
            for folder in dirs:
                self.folder_path = os.path.join(root, folder)
                try:
                    self.folder_hash = self.calculate_folder_hash(self.folder_path)
                    self.last_modified = self.get_formatted_time(os.path.getmtime(self.folder_path))
                except Exception as e:
                    print(f"Error processing folder: {e}")

                self.current_entries[self.folder_path] = {
                    "type": "folder",
                    "hash": self.folder_hash,
                    "last_modified": self.last_modified,
                }

                # Store in database
                self.database_instance.record_file_event(
                    directory_path=directory,
                    file_path=self.folder_path,
                    file_hash=self.folder_hash if self.folder_hash is not None else "folder_hash is None",
                    last_modified=self.last_modified if self.last_modified is not None else "last_modified time is None",
                    status='current'
                )

            for file in files:
                self.file_path = os.path.join(root, file)
                try:
                    self.file_hash = self.calculate_hash(self.file_path)
                    self.last_modified = self.get_formatted_time(os.path.getmtime(self.file_path))
                except Exception as e:
                    print(f"Error processing file: {e}")

                self.current_entries[self.file_path] = {
                    "type": "file",
                    "hash": self.file_hash,
                    "size": os.path.getsize(self.file_path),
                    "last_modified": self.last_modified,
                }

                # Store in database
                self.database_instance.record_file_event(
                    directory_path=directory,
                    file_path=self.file_path,
                    file_hash=self.file_hash if self.file_hash else "",
                    last_modified=self.last_modified if self.last_modified else "",
                    status='current'
                )

        return self.current_entries

    def calculate_hash(self, file_path: str) -> Optional[str]:
        """Calculate the SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(4096):
                    sha256.update(chunk)
                sha256.update(os.path.basename(file_path).encode())
            return sha256.hexdigest()
        except (IsADirectoryError, FileNotFoundError, PermissionError) as e:
            if self.logger is not None:
                self.logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            else:
                print(f"Logger is None. Error calculating hash for {file_path}: {str(e)}")
            return None

    def calculate_folder_hash(self, folder_path: str) -> str:
        """Calculate the SHA-256 hash of a folder."""
        sha256 = hashlib.sha256()
        folder = Path(folder_path)
        sha256.update(folder.name.encode())

        # Sort entries for consistent hashing
        entries = sorted(folder.iterdir(), key=lambda x: x.name)
        for entry in entries:
            sha256.update(entry.name.encode())
            if entry.is_dir():
                subfolder_hash = self.calculate_folder_hash(str(entry))
                sha256.update(subfolder_hash.encode())
            elif entry.is_file():
                file_hash = self.calculate_hash(str(entry))
                if file_hash:
                    sha256.update(file_hash.encode())
        
        return sha256.hexdigest()
