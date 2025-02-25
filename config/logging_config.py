import logging
import os
from pathlib import Path
import re


class configure_logger:
    def __init__(self):
         self.loggers = {}

    def _sanitize_directory_name(self, directory):
            """Sanitize directory name for safe use in filenames."""
            sanitized = re.sub(r'[\\/*?:"<>|]', '_', directory)
            # Replace path separators with underscores
            sanitized = sanitized.replace(os.sep, '_')
            # Remove leading underscores if any
            sanitized = sanitized.lstrip('_')
            return sanitized

    def _get_or_create_logger(self, directory):
        """Retrieve or create a logger for the specified directory."""
        normalized_dir = os.path.normpath(directory)
        if normalized_dir in self.loggers:
            print(normalized_dir)
            return self.loggers[normalized_dir]

        sanitized_name = self._sanitize_directory_name(normalized_dir)
        logger_name = f"FIM_{sanitized_name}"
        logger = logging.getLogger(logger_name)

        # Prevent adding duplicate handlers
        if not logger.handlers:
            log_file = f"FIM_Logging_{sanitized_name}.log"
            log_dir = os.path.join(os.path.dirname(__file__), "../logs")
            log_path = os.path.abspath(os.path.join(log_dir, log_file))
            
            # Ensure logs directory exists
            Path(log_dir).mkdir(parents=True, exist_ok=True)

            handler = logging.FileHandler(log_path)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        self.loggers[normalized_dir] = logger
        return logger
