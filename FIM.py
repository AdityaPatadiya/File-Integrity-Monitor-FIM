import os
import time
import json
import logging
from main1 import FIM_monitor
from backup import Backup

fim_instance = FIM_monitor()
backup_instance = Backup()

def monitor_changes(directory):
        """Monitor files and folders for integrity changes."""
        try:
            backup_instance.create_backup(directory)
            fim_instance.tracking_directory(directory)
            fim_instance.save_baseline(fim_instance.current_entries)
            baseline = fim_instance.load_baseline(fim_instance.BASELINE_FILE)
            # print(f"{baseline.values()}\n")
        except Exception as e:
            baseline = {}
            pass

        while True:
            try:
                

                updated_baseline = fim_instance.current_entries.copy()
                # print(f"updated_baseline: {updated_baseline}\n")
                baseline = updated_baseline
                # print(f"baseline: {baseline}\n")
                backup_baseline = baseline.copy()
                # print(f"backup_baseline: {backup_baseline}\n")

                try:
                    fim_instance.save_baseline(baseline)  # it will update the baseline.
                except Exception as e:
                    logging.error(f"Failed to save baseline securely: {e}")

                time.sleep(fim_instance.POLL_INTERVAL)
            except Exception as e:
                print(f"Error while monitoring: {e}")

def view_baseline():
    """View the current baseline data."""
    if os.path.exists(fim_instance.BASELINE_FILE):
        with open(fim_instance.BASELINE_FILE, "r") as f:
            print(json.dumps(json.load(f), indent=4))
    else:
        print("Baseline file not found.")

def reset_baseline(directory):
    """Reset the baseline file."""
    print("Resetting baseline and backup_baseline...")
    if os.path.exists(fim_instance.BASELINE_FILE):
        os.remove(fim_instance.BASELINE_FILE)

    backup_instance.create_backup(directory)
    if not backup_instance.backup_dir:
        print("backup_instance directory not initialized. Aborting reset.")
        return

    fim_instance.tracking_directory(directory)
    fim_instance.save_baseline(fim_instance.current_entries)
    print("Baseline and backup_baseline reset complete.")

def view_logs():
    """View the logs from the logging file."""
    if os.path.exists("FIM_Logging.log"):
            with open("FIM_Logging.log", "r") as log_file:
                print(log_file.read())
    else:
        print("Log file not found.")
