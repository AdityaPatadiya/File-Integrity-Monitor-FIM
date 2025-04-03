import os
import shutil
from datetime import datetime

class Backup:
    def __init__(self):
        self.backup_root = "/home/aditya/opensource/FIM_Backup"
        os.makedirs(self.backup_root, exist_ok=True)
        self.current_backup_dir = None  # Track current backup session

    def create_backup_session(self):
        """Create a timestamped parent backup directory"""
        timestamp = datetime.now().strftime(r"%Y%m%d_%H%M")
        self.current_backup_dir = os.path.join(
            self.backup_root,
            f"backup_{timestamp}"
        )
        os.makedirs(self.current_backup_dir)
        return self.current_backup_dir

    def create_backup(self, source_dir):
        """Backup a directory into the current backup session folder"""
        if not self.current_backup_dir:
            self.create_backup_session()

        if not os.path.exists(source_dir):
            print(f"Source directory {source_dir} does not exist.")
            return None

        try:
            dir_name = os.path.basename(os.path.normpath(source_dir))
            backup_path = os.path.join(
                self.current_backup_dir,
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
