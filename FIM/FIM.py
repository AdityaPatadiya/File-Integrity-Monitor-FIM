import os
import time
import json
import logging

from backup import Backup
from database import database_operation
from FIM.fim_utils import FIM_monitor
import logging_config


class monitor_changes:
    def __init__(self):
        self.reported_changes = {
            "added": {},
            "modified": {},
            "deleted": {},
        }
        self.backup_instance = Backup()
        self.fim_instance = FIM_monitor()
        self.database_instance = database_operation()
        self.current_file_hash = ""
        self.original_file_hash = ""
        self.current_folder_hash = ""
        self.original_folder_hash = ""

    def file_folder_addition(self, _path):
        if os.path.isfile(_path):
            if _path not in self.reported_changes["added"]:
                logging.warning(f"File added: {_path}")
                self.reported_changes["added"][_path] = {
                    "hash": self.current_file_hash,
                    "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path))
                }
        else:
            if _path not in self.reported_changes["added"]:
                logging.warning(f"Folder added: {_path}")
                self.reported_changes["added"][_path] = {
                    "hash": self.current_folder_hash,
                    "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path))
                }

    def file_folder_modification(self, _path):
        if os.path.isfile(_path):
            if _path in self.reported_changes["modified"]:
                if self.current_file_hash != self.reported_changes["modified"][_path]["hash"]:
                    logging.error(f"File modified: {_path}")
                    self.reported_changes["modified"][_path] = {
                        "hash": self.current_file_hash,
                        "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path))
                    }
            else:
                if self.current_file_hash != self.original_file_hash:
                    logging.error(f"File modified: {_path}")
                    self.reported_changes["modified"][_path] = {
                        "hash": self.current_file_hash,
                        "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path))
                    }
        else:
            if _path in self.reported_changes["modified"]:
                if self.current_folder_hash != self.reported_changes["modified"][_path]["hash"]:
                    logging.error(f"Folder modified: {_path}")
                    self.reported_changes["modified"][_path] = {
                        "hash": self.current_folder_hash,
                        "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path))
                    }
            else:
                if self.current_folder_hash != self.original_folder_hash:
                    logging.error(f"Folder modified: {_path}")
                    self.reported_changes["modified"][_path] = {
                        "hash": self.current_folder_hash,
                        "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path))
                    }

    def file_folder_deletion(self, _path):
        if os.path.isfile(_path):
            if _path not in self.reported_changes["deleted"]:
                logging.info(f"File deleted: {_path}")
                self.reported_changes["deleted"][_path] = {
                    "hash": self.original_file_hash,
                    "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path)) if os.path.exists(_path) else "N/A"
                }
        else:
            if _path not in self.reported_changes["deleted"]:
                logging.info(f"Folder deleted: {_path}")
                self.reported_changes["deleted"][_path] = {
                    "hash": self.original_folder_hash,
                    "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path)) if os.path.exists(_path) else "N/A"
                }

    def monitor_changes(self, directories, excluded_files):
        try:
            for directory in directories:
                self.backup_instance.create_backup(directory)

            if not os.path.exists(self.fim_instance.BASELINE_FILE):
                for directory in directories:
                    self.fim_instance.tracking_directory(directory)
                    self.fim_instance.save_baseline(self.fim_instance.current_entries)
                    self.fim_instance.load_baseline(self.fim_instance.BASELINE_FILE)
        except Exception as e:
            logging.error(f"Error while creating Baseline file: {e}")

        while True:
            try:
                for directory in directories:
                    if directory in excluded_files:
                        print(f"Directory {directory} excluded.")
                        continue
                    else:
                        self._monitor_directory(directory)
                time.sleep(self.fim_instance.POLL_INTERVAL)
            except Exception as e:
                logging.error(f"Error while monitoring directories: {e}")

    def _monitor_directory(self, directory):
        """Monitor files and folders for integrity changes."""
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    self.original_file_hash = self.database_instance.fetch_data(file_path)
                    if self.original_file_hash == None:
                        self.current_file_hash = self.fim_instance.calculate_hash(file_path)
                        if self.current_file_hash:
                            self.file_folder_addition(file_path)
                        else:
                            logging.error(f"Unrecognized Error {e} for: {file_path}")
                    else:
                        self.current_file_hash = self.fim_instance.calculate_hash(file_path)
                        if self.current_file_hash:
                            self.file_folder_modification(file_path)
                        else:
                            self.file_folder_deletion(file_path)
                except Exception as e:
                    print(f"Error processing the file: {file_path}, Error: {e}")

            for folder in dirs:
                folder_path = os.path.join(root, folder)
                try:
                    self.original_folder_hash = self.database_instance.fetch_data(folder_path)
                    if self.original_folder_hash == None:
                        self.current_folder_hash = self.fim_instance.calculate_folder_hash(folder_path)
                        if self.current_folder_hash:
                            self.file_folder_addition(folder_path)
                        else:
                            logging.error(f"Unrecognized Error {e} for: {folder_path}")
                    else:
                        self.current_folder_hash = self.fim_instance.calculate_folder_hash(folder_path)
                        if self.current_folder_hash:
                            self.file_folder_modification(folder_path)
                        else:
                            self.file_folder_deletion(folder_path)
                except Exception as e:
                    print(f"Error processing the folder: {folder_path}, Error: {e}")

    def view_baseline(self):
        """View the current baseline data."""
        if os.path.exists(self.fim_instance.BASELINE_FILE):
            with open(self.fim_instance.BASELINE_FILE, "r") as f:
                print(json.dumps(json.load(f), indent=4))
        else:
            print("Baseline file not found.")

    def reset_baseline(self, directories):
        """Reset the baseline file for multiple directories."""

        for directory in directories:
            if not os.path.exists(directory):
                print(f"Directory not found: {directory}. Skipping.")
                continue

            if os.path.exists(self.fim_instance.BASELINE_FILE):
                os.remove(self.fim_instance.BASELINE_FILE)

            self.backup_instance.create_backup(directory)
            if not self.backup_instance.backup_dir:
                print(f"Backup directory not initialized for {directory}. Skipping.")
                continue

            self.fim_instance.tracking_directory(directory)
            self.fim_instance.save_baseline(self.fim_instance.current_entries)

    def view_logs(self):
        """View the logs from the logging file."""
        log_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../logs/FIM_Logging.log"))
        if os.path.exists(log_file_path):
                with open(log_file_path, "r") as log_file:
                    print(log_file.read())
        else:
            print("Log file not found.")
