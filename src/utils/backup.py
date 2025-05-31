import os
import shutil
from datetime import datetime
import logging
import json

from src.utils.timestamp import timezone

class Backup:
    def __init__(self):
        self.backup_root = "../FIM_Backup/backup"
        os.makedirs(self.backup_root, exist_ok=True)
        self.meta_file_path = "../FIM_Backup/backup_metadata.json"  # where all the files hash and information will be stored.
        self.backup_log_path = "../FIMbackup/Backup_logs.json"  # where all the backup logs will be stored.

    def log_backup_session(self, current_log_data):
        """Create a timestamped parent backup directory"""
        with open(self.backup_log_path, "r") as file:
            if os.path.exists(self.backup_log_path):
                try:
                    existing_data = json.load(file)
                    if not isinstance(existing_data, list):
                        existing_data = []
                except (json.JSONDecodeError, FileNotFoundError):
                    existing_data = []
            else:
                existing_data = []

            backup_entry = {
                "timestamp": timezone()[0],
                "timezone": timezone()[1],
                "user": current_log_data.auth_user,
                "directory": current_log_data.source_dir,
                "backup_type": current_log_data.backup_type,
                "status": current_log_data.backup_status,
                "duration_seconds": current_log_data.backup_duration,
                "file_changes": current_log_data.files_changes
            }
            existing_data.append(backup_entry)

        with open(self.backup_log_path, 'w') as file:
            json.dump(existing_data, file, indent=4)

    def create_backup(self, source_dir, auth_username=None):
        """Backup a directory into the current backup session folder"""
        if not self.backup_root:
            os.makedirs(self.backup_root, exist_ok=True)

        if not os.path.exists(source_dir):
            print(f"Source directory {source_dir} does not exist.")
            return None

        try:
            dir_name = os.path.basename(os.path.normpath(source_dir))
            backup_path = os.path.join(
                self.backup_root,
                dir_name
            )

            shutil.copytree(
                source_dir,
                backup_path,
                ignore=shutil.ignore_patterns('.*')
            )

            print(f"Backed up '{dir_name}' to:\n{backup_path}")
            return backup_path

        except Exception as e:
            print(f"Backup failed for {source_dir}: {str(e)}")
            return None
