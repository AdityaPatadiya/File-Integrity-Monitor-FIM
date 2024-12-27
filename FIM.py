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
        original_content_map = {}
        backup_content_map = {}
        backup_baseline = {}
        try:
            backup_instance.create_backup(directory)
            backup_instance.create_and_load_backup_hash()
            backup_baseline = backup_instance.backup_entries
            # for key in list(backup_baseline.keys()):
            #     normalized_key = os.path.abspath(key)
            #     if normalized_key != key:
            #         backup_baseline[normalized_key] = backup_baseline.pop(key)
            baseline = fim_instance.load_baseline(fim_instance.BASELINE_FILE)
        except Exception as e:
            logging.error(f"Failed to load baseline: {e}")
            baseline = {}

        while True:
            try:
                updated_baseline = baseline.copy()
                fim_instance.tracking_directory(directory)

                for (current_path, current_metadata), (backup_path, backup_metadata) in zip(fim_instance.current_entries.items(), backup_baseline.items()):
                    if current_metadata["type"] == "file" and backup_metadata["type"] == "file":
                        current_hash_value = current_metadata.get("hash")
                        backup_hash_value = backup_metadata.get("hash")
                        if current_hash_value is None or backup_hash_value is None:
                            logging.warning(f"No hash value for file: {current_path if current_hash_value is None else backup_path}")
                            continue
                        original_content_map[current_path] = current_hash_value
                        backup_content_map[backup_path] = backup_hash_value
                        # print(f"original_content_map_1: {original_content_map}\n")
                        # print(f"backup_content_map_1: {backup_content_map}\n")
                    elif current_metadata["type"] == "folder" and backup_metadata["type"] == "folder":
                        current_hash_value = current_metadata.get("hash")
                        backup_hash_value = backup_metadata.get("hash")
                        if current_hash_value == None or backup_hash_value == None:
                            logging.warning(f"No hash value for folder: {current_path if current_hash_value == None else backup_path}")
                        original_content_map[current_path] = current_hash_value
                        backup_content_map[backup_path] = backup_hash_value
                        # print(f"original_content_map_2: {original_content_map}\n")
                        # print(f"backup_content_map_2: {backup_content_map}\n")

                    else:
                        print("'type' is missing from baseilne files.")
                        continue

                # print(f"original_content_map: {original_content_map}\n")
                # print(f"backup_content_map: {backup_content_map}\n")

                current_keys, current_values = set(original_content_map.keys()), set(original_content_map.values())
                # print(f"current_keys: {current_keys}\n")
                backup_keys, backup_values = set(backup_content_map.keys()), set(backup_content_map.values())
                # print(f"backup_keys: {backup_keys}\n")

                added_values = current_values - backup_values
                # print(f"added_key: {added_key}\n")
                common_values = current_values & backup_values
                # print(f"common_key: {common_keys}\n")
                deleted_values = backup_values - current_values
                # print(f"deleted_key: {deleted_keys}\n")

                for key in common_values:
                    current_entry = original_content_map.get(key, {})
                    backup_entry = backup_content_map.get(key, {})

                    if not isinstance(current_entry, dict) or not isinstance(backup_entry, dict):
                        logging.error(f"Invalid entry format for key: {key}")
                        continue

                    if "type" not in current_entry or "type" not in backup_entry:
                        logging.error(f"Missing 'type' key for key: {key}")
                        continue

                    if current_entry["type"] == "file":
                        if "hash" not in current_entry or "hash" not in backup_entry:
                            logging.error(f"Missing 'hash' key for file: {key}")
                            continue

                        if current_entry["hash"] != backup_entry["hash"]:
                            logging.warning(f"File modified: {key}")
                    elif "last_modified" in current_entry and "last_modified" in backup_entry:
                        if current_entry["last_modified"] != backup_entry["last_modified"]:
                            logging.warning(f"Folder modified: {key}")

                for key in added_values:
                    entry = fim_instance.current_entries.get(key, {})
                    if not isinstance(entry, dict) or "type" not in entry:
                        logging.error(f"Invalid entry format for added key: {key}")
                        continue

                    if entry["type"] == "file":
                        logging.info(f"New File is added: {key}")
                    else:
                        logging.info(f"New folder is added: {key}")

                for key in deleted_values:
                    if not isinstance(key, dict) or "type" not in key:
                        logging.error(f"Invalid or missing 'type' key for deleted key: {key}")
                        continue

                    if entry["type"] == "file":
                        logging.warning(f"File deleted: {key}")
                    else:
                        logging.warning(f"folder deleted: {key}")

                updated_baseline = fim_instance.current_entries.copy()
                baseline = updated_baseline
                backup_baseline = baseline.copy()

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
    if os.path.exists(fim_instance.BASELINE_FILE) and os.path.exists(backup_instance.BACKUP_BASELINE_FILE):
        os.remove(fim_instance.BASELINE_FILE)
        os.remove(backup_instance.BACKUP_BASELINE_FILE)

    backup_instance.create_backup(directory)
    if not backup_instance.backup_dir:
        print("backup_instance directory not initialized. Aborting reset.")
        return

    fim_instance.tracking_directory(directory)
    fim_instance.save_baseline(fim_instance.current_entries)
    fim_instance.tracking_directory(backup_instance.backup_dir)
    backup_instance.create_and_load_backup_hash()
    print("Baseline and backup_baseline reset complete.")

def view_logs():
    """View the logs from the logging file."""
    if os.path.exists("FIM_Logging.log"):
            with open("FIM_Logging.log", "r") as log_file:
                print(log_file.read())
    else:
        print("Log file not found.")
