import os
import shutil
from datetime import datetime


class Backup:
    def __init__(self):
        self.backup_directory = "E:/coding/PYTHON/FIM_Backup/"

    def normalized_path(self, path):
        return os.path.normpath(path)

    def create_backup(self, source_dir):
        """Create a backup directory for monitored directory."""
        if not os.path.exists(source_dir):
            print(f"Source directory {source_dir} does not exist.")
            return

        dir_name = os.path.basename(os.path.normpath(source_dir))
        timestamp = datetime.now().strftime(r"%Y%m%d_%H%M")
        backup_dir = os.path.join(
            self.backup_directory, 
            f"backup_{dir_name}_{timestamp}"
        )

        try:
            # Clear existing backup if it exists
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
                print("existing backup cleared.\n")

            shutil.copytree(source_dir, backup_dir, 
                          ignore=shutil.ignore_patterns('.*'))
            print(f"Backup created for {dir_name} at {backup_dir}")
        except Exception as e:
            print(f"Backup failed for {source_dir}: {str(e)}")
