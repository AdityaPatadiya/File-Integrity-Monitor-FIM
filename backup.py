import os
import json
import shutil
from main1 import FIM_monitor
from datetime import datetime


class Backup:
    def __init__(self):
        self.BACKUP_BASELINE_FILE = "E:/coding/PYTHON/FIM_Backup/baseline_for_backup.json"
        self.backup_directory = "E:/coding/PYTHON/FIM_Backup/"
        self.backup_dir = None
        self.backup_entries = {}
        self.fim_instance = FIM_monitor()

    def normalized_path(self, path):
        return os.path.normpath(path)

    def create_backup(self, source_dir):
        if not os.path.exists(source_dir):
            print(f"Source directory {source_dir} does not exist.")
            return

        timestamp = datetime.now().strftime(r"%Y_%m_%d_%H_%M_%S")
        self.backup_dir = self.normalized_path(os.path.join(self.backup_directory, f"backup_{timestamp}"))
        os.makedirs(self.backup_dir, exist_ok=True)

        backup_baseline = {}
        try:
            for item in os.listdir(source_dir):
                item_path = os.path.join(source_dir, item)
                if item_path == self.backup_dir:
                    continue
                
                dest_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(item_path):
                    shutil.copytree(item_path, dest_path)
                    backup_baseline[dest_path] = {
                        "type": "folder",
                        "hash": self.fim_instance.calculate_folder_hash(item_path),
                        "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(item_path)),
                    }
                else:
                    shutil.copy2(item_path, dest_path)
                    backup_baseline[dest_path] = {
                        "type": "file",
                        "hash": self.fim_instance.calculate_hash(dest_path),
                        "size": os.path.getsize(dest_path),
                        "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(item_path)),
                    }

            backup_baseline = {self.normalized_path(k): v for k, v in backup_baseline.items()}
            
            with open(self.BACKUP_BASELINE_FILE, "w") as f:
                json.dump(backup_baseline, f, indent=4)

            print(f"Backup created successfully at {self.backup_dir} and baseline saved.")
        except Exception as e:
            print(f"An error occurred during backup: {e}")

    def create_and_load_backup_hash(self):
        """Create and load the hash for the backup directory."""
        for root, dirs, files in os.walk(self.backup_dir):
            for folder in dirs:
                folder_path = os.path.join(root, folder)
                self.backup_entries[folder_path] = {
                    "type": "folder",
                    "hash": self.fim_instance.calculate_folder_hash(folder_path),
                    "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(folder_path)),
                }

            for file in files:
                file_path = os.path.join(root, file)
                self.backup_entries[file_path] = {
                    "type": "file",
                    "hash": self.fim_instance.calculate_hash(file_path),
                    "size": os.path.getsize(file_path),
                    "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(folder_path)),
                }
        
        self.backup_entries = {self.normalized_path(k): v for k, v in self.backup_entries.items()}
        
        with open(self.BACKUP_BASELINE_FILE, "w") as f:
            json.dump(self.backup_entries, f, indent=4)
        
        return self.fim_instance.load_baseline(self.BACKUP_BASELINE_FILE)

