import logging
import os
from pathlib import Path
import re


class configure_logger:
    def __init__(self):
         self.loggers = {}

    def _sanitize_directory_name(self, directory):
            """Sanitize directory name for safe use in filenames."""
            print("_sanitize_directory_name method called.\n")
            sanitized = re.sub(r'[\\/*?:"<>|]', '_', directory)
            sanitized = sanitized.replace(os.sep, '__')
            sanitized = sanitized.lstrip('_')
            return sanitized

    def _get_or_create_logger(self, directory):
        """Retrieve or create a logger for the specified directory."""
        print("_get_or_create_logger method called.\n")
        try:
            normalized_dir = os.path.normpath(directory)
            print(f"normalized_directory: {normalized_dir}")
            if not os.path.exists(normalized_dir):
                 raise FileNotFoundError(f"Directory {normalized_dir} does not exist.")

            if normalized_dir in self.loggers:
                return self.loggers[normalized_dir]

            sanitized_name = self._sanitize_directory_name(normalized_dir)
            logger_name = f"FIM_{sanitized_name}"
            logger = logging.getLogger(logger_name)
            print(f"logger for [{logger_name}(logger_name)]: {logger}\n")

            if not logger.handlers:
                log_dir = os.path.abspath(os.path.join(
                    os.path.dirname(__file__), "..", "logs"
                ))
                print(f"log_dir: {log_dir}\n")
                Path(log_dir).mkdir(parents=True, exist_ok=True)

                log_file = os.path.join(log_dir, f"FIM_Logging_{sanitized_name}.log")
                print(f"log_file: {log_file}\n")

                handler = logging.FileHandler(log_file)
                formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(logging.INFO)
                logger.propagate = False  # prevent duplicates logging

                logger.info(f"Logger initialize for {normalized_dir}")

            self.loggers[normalized_dir] = logger
            print(f"logger is: {logger}\n")
            return logger

        except Exception as e:
             print(f"Error creating logger for {directory}: {str(e)}")

    def shutdown(self):
        """Clean up all logging resources"""
        print("shutdown method is called.")
        for logger in self.loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        self.loggers.clear()
