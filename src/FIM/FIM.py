import os
import time
import json
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.utils.backup import Backup
from src.utils.database import database_operation
from src.FIM.fim_utils import FIM_monitor
from config.logging_config import configure_logger


class FIMEventHandler(FileSystemEventHandler):
    def __init__(self, parent, logger):
        super().__init__()
        self.parent: monitor_changes = parent
        self.logger = logger
        self.directory_path = None

    def _get_directory_path(self, event_path):
        """Extract monitored directory path from event path"""
        for dir_path in self.parent.current_directories:
            if event_path.startswith(dir_path):
                return dir_path
        return os.path.dirname(event_path)

    def on_created(self, event):
        try:
            dir_path = self._get_directory_path(event.src_path)
            last_modified = self.parent.fim_instance.get_formatted_time(os.path.getmtime(event.src_path))

            if not event.is_directory:
                file_hash = self.parent.fim_instance.calculate_hash(event.src_path)
                self.parent.database_instance.record_file_event(
                    directory_path=dir_path,
                    file_path=event.src_path,
                    file_hash=file_hash,
                    last_modified=last_modified,
                    status='added'
                )
            else:
                folder_hash = self.parent.fim_instance.calculate_folder_hash(event.src_path)
                self.parent.database_instance.record_file_event(
                    directory_path=dir_path,
                    file_path=event.src_path,
                    file_hash=folder_hash,
                    last_modified=last_modified,
                    status='added'
                )

            self.parent.file_folder_addition(event.src_path)

        except Exception as e:
            self.logger.error(f"Creation error: {str(e)}")

    def on_modified(self, event):
        try:
            if event.is_directory:
                return

            dir_path = self._get_directory_path(event.src_path)
            last_modified = self.parent.fim_instance.get_formatted_time(os.path.getmtime(event.src_path))
            current_hash = self.parent.fim_instance.calculate_hash(event.src_path)

            original_hash = self.parent.database_instance.get_current_baseline(dir_path).get(event.src_path, {}).get('hash', '')

            if original_hash != current_hash:
                self.parent.database_instance.record_file_event(
                    directory_path=dir_path,
                    file_path=event.src_path,
                    file_hash=current_hash,
                    last_modified=last_modified,
                    status='modified'
                )
                self.parent.file_folder_modification(event.src_path)

        except Exception as e:
            self.logger.error(f"Modification error: {str(e)}")

    def on_deleted(self, event):
        try:
            dir_path = self._get_directory_path(event.src_path)

            if not event.is_directory:
                baseline = self.parent.database_instance.get_current_baseline(dir_path)
                file_hash = baseline.get(event.src_path, {}).get('hash', '')
                last_modified = baseline.get(event.src_path, {}).get('last_modified', '')

                self.parent.database_instance.record_file_event(
                    directory_path=dir_path,
                    file_path=event.src_path,
                    file_hash=file_hash,
                    last_modified=last_modified,
                    status='deleted'
                )
            self.parent.file_folder_deletion(event.src_path)

        except Exception as e:
            self.logger.error(f"Deletion error: {str(e)}")

class monitor_changes:
    def __init__(self):
        self.logs_dir = Path(__file__).resolve().parent.parent / "../logs"
        self.logs_dir.mkdir(exist_ok=True, parents=True)
        self.reported_changes = {
            "added": {},
            "modified": {},
            "deleted": {},
        }
        self.backup_instance = Backup()
        self.fim_instance = FIM_monitor()
        self.database_instance = database_operation()
        self.configure_logger = configure_logger()
        self.observer = Observer()
        self.current_file_hash = ""
        self.original_file_hash = ""
        self.current_folder_hash = ""
        self.original_folder_hash = ""
        self.current_logger = None
        self.current_directories = []
        self.event_handlers = []

    def file_folder_addition(self, _path):
        if os.path.isfile(_path):
            if _path not in self.reported_changes["added"]:
                self.current_logger.warning(f"File added: {_path}")
                self.reported_changes["added"][_path] = {
                    "hash": self.current_file_hash,
                    "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path))
                }
        else:
            if _path not in self.reported_changes["added"]:
                self.current_logger.warning(f"Folder added: {_path}")
                self.reported_changes["added"][_path] = {
                    "hash": self.current_folder_hash,
                    "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path))
                }

    def file_folder_modification(self, _path):
        if os.path.isfile(_path):
            if _path in self.reported_changes["modified"]:
                if self.current_file_hash != self.reported_changes["modified"][_path]["hash"]:
                    self.current_logger.error(f"File modified: {_path}")
                    self.reported_changes["modified"][_path] = {
                        "hash": self.current_file_hash,
                        "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path))
                    }
            else:
                if self.current_file_hash != self.original_file_hash:
                    self.current_logger.error(f"File modified: {_path}")
                    self.reported_changes["modified"][_path] = {
                        "hash": self.current_file_hash,
                        "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path))
                    }
        else:
            if _path in self.reported_changes["modified"]:
                if self.current_folder_hash != self.reported_changes["modified"][_path]["hash"]:
                    self.current_logger.error(f"Folder modified: {_path}")
                    self.reported_changes["modified"][_path] = {
                        "hash": self.current_folder_hash,
                        "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path))
                    }
            else:
                if self.current_folder_hash != self.original_folder_hash:
                    self.current_logger.error(f"Folder modified: {_path}")
                    self.reported_changes["modified"][_path] = {
                        "hash": self.current_folder_hash,
                        "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path))
                    }

    def file_folder_deletion(self, _path):
        if os.path.isfile(_path):
            if _path not in self.reported_changes["deleted"]:
                self.current_logger.warning(f"File deleted: {_path}")
                self.reported_changes["deleted"][_path] = {
                    "hash": self.original_file_hash,
                    "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path)) if os.path.exists(_path) else "N/A"
                }
        else:
            if _path not in self.reported_changes["deleted"]:
                self.current_logger.warning(f"Folder deleted: {_path}")
                self.reported_changes["deleted"][_path] = {
                    "hash": self.original_folder_hash,
                    "last_modified": self.fim_instance.get_formatted_time(os.path.getmtime(_path)) if os.path.exists(_path) else "N/A"
                }

    def monitor_changes(self, directories, excluded_files):
        """Monitor specified directories for changes using Watchdog."""
        try:
            self.current_directories = directories

            for directory in self.current_directories:
                if not os.path.exists(directory):
                    raise FileNotFoundError(f"Directory {directory} does not exist")
                try:
                    self.backup_instance.create_backup(directory)
                except Exception as e:
                    print(f"Failed to create backup for {directory}")
                    continue

                baseline = self.fim_instance.tracking_directory(directory)
                for path, data in baseline.items():
                    self.database_instance.record_file_event(
                        directory_path=directory,
                        file_path=path,
                        file_hash=data['hash'],
                        last_modified=data['last_modified'],
                        status='current'
                    )

            for directory in self.current_directories:
                if directory in excluded_files:
                    continue

                logger = self.configure_logger._get_or_create_logger(directory)
                logger.info(f"Starting monitoring for {directory}")

                event_handler = FIMEventHandler(self, logger)
                event_handler.directory_path = directory
                self.observer.schedule(event_handler, directory, recursive=True)
                self.event_handlers.append(event_handler)

            self.observer.start()
            try:
                while True:
                    time.sleep(1)  # Main thread sleep
            except KeyboardInterrupt:
                print("\nShutdown down...")
                self.observer.stop()
                self.observer.join()
                self.configure_logger.shutdown()
                print("Shutdown complete.")
        except Exception as e:
            if self.current_logger:
                self.current_logger.error(f"Monitoring error: {e}")
            else:
                self.observer.stop()
                self.observer.join()  # Ensure observer is stopped even on error
                self.configure_logger.shutdown()

    def _save_reported_changes(self):
        for change_type, changes in self.reported_changes.items():
            for path, data in changes.items():
                directory = os.path.dirname(path)
                self.database_instance.record_file_event(
                    directory_path=directory,
                    file_path=path,
                    file_hash=data['hash'],
                    last_modified=data['last_modified'],
                    status=change_type
                )

    def view_baseline(self):
        """View ALL baselines with datetime serialization support"""
        try:
            directories = self.database_instance.get_all_monitored_directories()

            if not directories:
                print("No baseline data exists in database")
                return

            for directory in directories:
                print(f"\nBaseline for {directory}:")
                baseline = self.database_instance.get_current_baseline(directory)

                class DateTimeEncoder(json.JSONEncoder):
                    def default(self, obj):
                        if isinstance(obj, datetime):
                            return obj.strftime("%Y-%m-%d %H:%M:%S")
                        return super().default(obj)

                print(json.dumps(baseline, indent=4, cls=DateTimeEncoder))
                
        except Exception as e:
            print(f"Error viewing baseline: {str(e)}")

    def reset_baseline(self, directories):
        """Safely reset baseline with transaction support"""
        for directory in directories:
            try:
                if not Path(directory).exists():
                    print(f"Directory not found: {directory}")
                    continue

                with self.database_instance.transaction() as cursor:
                    cursor.execute('DELETE FROM file_metadata WHERE directory_path = ?', (directory,))
                    self.fim_instance.tracking_directory(directory)
                    print(f"Reset baseline for {directory}")
            except Exception as e:
                print(f"Failed resetting baseline for {directory}: {str(e)}")

    def view_logs(self, directory=None):
        """View logs safely with path validation"""
        try:
            if directory:
                norm_dir = Path(directory).resolve()
                if not norm_dir.exists():
                    print(f"Directory {directory} does not exist")
                    return

                log_file = self.logs_dir / f"FIM_{norm_dir.name}.log"
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        print(f.read())
                else:
                    print(f"No logs for {directory}")
            else:
                for log_path in self.logs_dir.glob("FIM_*.log"):
                    print(f"\n=== Logs for {log_path.stem} ===")
                    with open(log_path, 'r', encoding='utf-8') as f:
                        print(f.read(4096))  # Show first 4KB per file
        except Exception as e:
            print(f"Log viewing error: {str(e)}")
