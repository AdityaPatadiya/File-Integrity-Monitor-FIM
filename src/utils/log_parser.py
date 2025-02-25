import os
import re
import pandas as pd

def parse_log_file(log_file_path):
    log_entries = []

    try:
        with open(log_file_path, 'r') as file:
            for line in file:
                match = re.match(r'(\d+-\d+-\d+ \d+:\d+:\d+,\d+) - (\w+) - (.+)', line)
                if match:
                    timestamp, log_level, message = match.groups()
                    log_entries.append({
                        'timestamp': timestamp,
                        'log_level': log_level,
                        'message': message
                    })
    except FileNotFoundError:
        print(f"Log file '{log_file_path}' not found.")

    return pd.DataFrame(log_entries)

# Test
if __name__ == "__main__":
    log_folder_path = 'logs'
    for file in os.listdir(log_folder_path):
        file_path = os.path.join(log_folder_path, file)
        log_df = parse_log_file(file_path)
        print(log_df.head() if not log_df.empty else "No logs found.")
