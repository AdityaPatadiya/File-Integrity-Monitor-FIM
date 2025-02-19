import os
import shutil
from datetime import datetime


class Backup:
    def __init__(self):
        self.backup_directory = "E:/coding/PYTHON/FIM_Backup/"
        self.backup_dir = None

    def normalized_path(self, path):
        return os.path.normpath(path)

    def create_backup(self, source_dir):
        """Create a backup directory for monitored directory."""
        if not os.path.exists(source_dir):
            print(f"Source directory {source_dir} does not exist.")
            return

        timestamp = datetime.now().strftime(r"%Y%m%d_%H%M")
        self.backup_dir = self.normalized_path(os.path.join(self.backup_directory, f"backup_{timestamp}"))
        os.makedirs(self.backup_dir, exist_ok=True)

        
        try:
            for item in os.listdir(source_dir):
                item_path = os.path.join(source_dir, item)
                if item_path == self.backup_dir:
                    continue
                
                dest_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(item_path):
                    shutil.copytree(item_path, dest_path)
                else:
                    shutil.copy2(item_path, dest_path)

            print(f"Backup created successfully at {self.backup_dir}.")
        except FileExistsError:
            print(f"{self.backup_dir} is already exist. for updated backup, please run the FIM again after a minute.")
        except Exception as e:
            print(f"An error occurred during backup: {e}")
