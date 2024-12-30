import os
import argparse
from FIM import monitor_changes

monitor_changes = monitor_changes()

def main():
    parser = argparse.ArgumentParser(description="File Integrity Monitor CLI Tool")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring the directory")
    parser.add_argument("--view-baseline", action="store_true", help="View the current baseline data")
    parser.add_argument("--reset-baseline", action="store_true", help="Reset the baseline data")
    parser.add_argument("--view-logs", action="store_true", help="View the log file")
    parser.add_argument("--dir", type=str, default="test", help="Directory to monitor (default: 'test')")

    args = parser.parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Directory where the script is located
    monitored_dir = os.path.join(script_dir, args.dir)

    if args.view_baseline:
        monitor_changes.view_baseline()
    if args.reset_baseline:
        monitor_changes.reset_baseline(monitored_dir)
    if not (args.monitor or args.view_baseline or args.reset_baseline or args.view_logs):
        parser.print_help()
    if args.view_logs:
        monitor_changes.view_logs()
    if args.monitor:
        if not os.path.exists(monitored_dir):
            print(f"Creating monitored directory: {monitored_dir}")
            os.makedirs(monitored_dir)
        print("Starting File Integrity Monitor...")
        try:
            monitor_changes.monitor_changes(monitored_dir)
            print(monitored_dir)
        except KeyboardInterrupt:
            print("\nFile Integrity Monitor stopped.")

if __name__ == "__main__":
    main()
