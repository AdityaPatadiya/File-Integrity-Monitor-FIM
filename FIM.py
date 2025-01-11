import os
import time
import json
import logging
from backup import Backup
from database import database_operation
from main1 import FIM_monitor


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

    def monitor_changes(self, directories, excluded_files):
        try:
            if not os.path.exists(self.fim_instance.BASELINE_FILE):
                for directory in directories:
                    self.backup_instance.create_backup(directory)
                    self.fim_instance.tracking_directory(directory)
                    self.fim_instance.save_baseline(self.fim_instance.current_entries)
                    self.fim_instance.load_baseline(self.fim_instance.BASELINE_FILE)
        except Exception as e:
            logging.error

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
                for folder in dirs:
                    folder_path = os.path.join(root, folder)
                    original_folder_hash = self.database_instance.fetch_data(folder_path)

                    if original_folder_hash:
                        current_folder_hash = self.fim_instance.calculate_folder_hash(folder_path)
                        if current_folder_hash:
                            if folder_path in self.reported_changes["modified"]:
                                if current_folder_hash != self.reported_changes["modified"][folder_path]:
                                    logging.error(f"Folder modified: {folder_path}")
                                    self.reported_changes["modified"][folder_path] = current_folder_hash
                            else:
                                if current_folder_hash != original_folder_hash:
                                    logging.error(f"Folder modified: {folder_path}")
                                    self.reported_changes["modified"][folder_path] = current_folder_hash
                        else:
                            if original_folder_hash in self.reported_changes["deleted"][folder_path]:
                                continue
                            else:
                                logging.info(f"Folder deleted: {folder_path}")
                                self.reported_changes["deleted"][folder_path] = original_folder_hash
                    else:
                        if current_folder_hash:
                            if folder_path in self.reported_changes["added"][folder_path]:
                                continue
                            else:
                                logging.warning(f"Folder added: {folder_path}")
                                self.reported_changes["added"][folder_path] = current_folder_hash
                        else:
                            logging.error(f"Unrecognized Error for: {folder_path}")

                for file in files:
                    file_path = os.path.join(root, file)
                    original_file_hash = self.database_instance.fetch_data(file_path)

                    if original_file_hash:
                        current_file_hash = self.fim_instance.calculate_hash(file_path)
                        if current_file_hash:
                            if file_path in self.reported_changes["modified"]:
                                if current_file_hash != self.reported_changes["modified"][file_path]:
                                    logging.error(f"File modified: {file_path}")
                                    self.reported_changes["modified"][file_path] = current_file_hash
                            else:
                                if current_file_hash != original_file_hash:
                                    logging.error(f"File modified: {file_path}")
                                    self.reported_changes["modified"][file_path] = current_file_hash
                        else:
                            if original_file_hash in self.reported_changes["deleted"][file_path]:
                                continue
                            else:
                                logging.info(f"File deleted: {file_path}")
                                self.reported_changes["deleted"][file_path] = original_file_hash
                    else:
                        if current_file_hash:
                            if file_path in self.reported_changes["added"][file_path]:
                                continue
                            else:
                                logging.warning(f"File added: {file_path}")
                                self.reported_changes["added"][file_path] = current_file_hash
                        else:
                            logging.error(f"Unrecognized Error for: {file_path}")

    def view_baseline(self):
        """View the current baseline data."""
        if os.path.exists(self.fim_instance.BASELINE_FILE):
            with open(self.fim_instance.BASELINE_FILE, "r") as f:
                print(json.dumps(json.load(f), indent=4))
        else:
            print("Baseline file not found.")

    def reset_baseline(self, directory):
        """Reset the baseline file."""
        print("Resetting baseline and backup_baseline...")
        if os.path.exists(self.fim_instance.BASELINE_FILE):
            os.remove(self.fim_instance.BASELINE_FILE)

        self.backup_instance.create_backup(directory)
        if not self.backup_instance.backup_dir:
            print("self.backup_instance directory not initialized. Aborting reset.")
            return

        self.fim_instance.tracking_directory(directory)
        self.fim_instance.save_baseline(self.fim_instance.current_entries)
        print("Baseline and backup_baseline reset complete.")

    def view_logs(self):
        """View the logs from the logging file."""
        if os.path.exists("FIM_Logging.log"):
                with open("FIM_Logging.log", "r") as log_file:
                    print(log_file.read())
        else:
            print("Log file not found.")
