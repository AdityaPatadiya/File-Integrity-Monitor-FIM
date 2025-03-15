import os
import time
import json
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
        print("FIMEventHandler class initialized.\n")

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
        self.reported_changes = {
            "added": {},
            "modified": {},
            "deleted": {},
        }
        self.backup_instance = Backup()
        self.fim_instance = FIM_monitor()
        self.database_instance = database_operation()
        self.configre_logger = configure_logger()
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
            print(f"current_directories: {directories}\n")

            for directory in self.current_directories:
                print(f"directory: {directory}.\n")
                if not os.path.exists(directory):
                    raise FileNotFoundError(f"Directory {directory} does not exist")
                print(f"Creating backup for {directory}")
                try:
                    self.backup_instance.create_backup(directory)
                except Exception as e:
                    print(f"Failed to create backup for {directory}")
                    continue

                baseline = self.fim_instance.tracking_directory(directory)
                print(f"baseline: {baseline}\n")
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
                    print(f"Directory {directory} excluded.")
                    continue

                logger = self.configre_logger._get_or_create_logger(directory)
                logger.info(f"Starting monitoring for {directory}")

                event_handler = FIMEventHandler(self, logger)
                event_handler.directory_path = directory
                self.observer.schedule(event_handler, directory, recursive=True)
                self.event_handlers.append(event_handler)
                print(f"self.event_handlers: {self.event_handlers}\n")

            self.observer.start()
            try:
                while True:
                    time.sleep(1)  # Main thread sleep
                    print("while loop of monitor_changes called.\n")
            except KeyboardInterrupt:
                print("\nShutdown down...")
                self.observer.stop()
                self.observer.join()
                self.configre_logger.shutdown()
                self.database_instance.close_connection()
                print("Shutdown complete.")
        except Exception as e:
            if self.current_logger:
                self.current_logger.error(f"Monitoring error: {e}")
            else:
                print(f"Critical error: {e}")
                self.observer.stop()
                self.observer.join()  # Ensure observer is stopped even on error
                self.configre_logger.shutdown()
                self.database_instance.close_connection()

    def _save_reported_changes(self):
        print("_save_reported_changes called.\n")
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
        """View current baseline from database"""
        if not self.current_directories:
            print("No directories being monitored")
            return

        for directory in self.current_directories:
            print(f"\nBaseline for {directory}:")
            baseline = self.database_instance.get_current_baseline(directory)
            print(json.dumps(baseline, indent=4))

    def reset_baseline(self, directories):
        """Reset baseline in database"""
        for directory in directories:
            if not os.path.exists(directory):
                print(f"Directory not found: {directory}. Skipping.")
                continue

            self.database_instance.delete_directory_records(directory)
            self.fim_instance.tracking_directory(directory)

            print(f"Reset baseline for {directory}")

    def view_logs(self, directory=None):
        """View logs for a specific directory or all directories."""
        if directory:
            normalized_dir = os.path.normpath(directory)
            sanitized_name = self.configre_logger._sanitize_directory_name(normalized_dir)
            log_file = os.path.join("logs", f"FIM_Logging_{sanitized_name}.log")
            log_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", log_file))
            if os.path.exists(log_path):
                with open(log_path, "r") as log_file:
                    print(log_file.read())
            else:
                print(f"No logs found for {directory}.")
        else:
            log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../logs"))
            for log_file in os.listdir(log_dir):
                if log_file.startswith("FIM_Logging_") and log_file.endswith(".log"):
                    print(f"=== Logs for {log_file} ===")
                    with open(os.path.join(log_dir, log_file), "r") as f:
                        print(f.read())
