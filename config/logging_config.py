import os
import logging

log_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../logs/FIM_Logging.log"))

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
