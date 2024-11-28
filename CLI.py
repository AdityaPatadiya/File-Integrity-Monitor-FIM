import argparse
import os
from FIM import monitor_changes, view_baseline, reset_baseline, view_logs

def main():
    parser = argparse.ArgumentParser(description="File Integrity Monitor CLI Tool")
    parser.add_argument("--monitor", action="store_true", help="Start monitoring the directory")
    parser.add_argument("--view-baseline", action="store_true", help="View the current baseline data")
    parser.add_argument("--reset-baseline", action="store_true", help="Reset the baseline data")
    parser.add_argument("--view-logs", action="store_true", help="View the log file")
    parser.add_argument("--dir", type=str, default="./test", help="Directory to monitor (default: './test')")

    args = parser.parse_args()

    if args.monitor:
        if not os.path.exists(args.dir):
            print(f"Creating monitored directory: {args.dir}")
            os.makedirs(args.dir)
        print("Starting File Integrity Monitor...")
        try:
            monitor_changes(args.dir)
        except KeyboardInterrupt:
            print("\nFile Integrity Monitor stopped.")
    elif args.view_baseline:
        view_baseline()
    elif args.reset_baseline:
        reset_baseline(args.dir)
    elif args.view_logs:
        view_logs()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
